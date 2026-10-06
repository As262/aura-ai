# -*- coding: utf-8 -*-
"""
Realistic conversation corpus for the interest model.

WHY THIS EXISTS
---------------
The previous training data was a lookup table. Five hard-coded lists of reply
strings, one per interest level, and the label *was* the list the string came
from. A model trained on that learns to invert the generator, reports 96%
validation accuracy, and tells you nothing about a real chat - because in the
real world nobody replies with "OMG YES!! that's exactly what i was thinking!!"
and plenty of genuinely interested people reply "haan" or "sounds good".

This module models the thing we actually want to predict instead. Each
conversation is produced by two people with:

* a **latent interest** that varies over the conversation along an arc
  (steady, cooling off, warming up, spike-then-fade, revival),
* a **persona** whose habits are independent of interest - how wordy they are,
  whether they use emoji at all, how fast they answer anyone, what register
  they text in (English / Hinglish / Gen-Z / formal), how often they typo.

Interest then leaks into *behaviour*, not into vocabulary: reply latency,
whether they ask something back, whether they pick up your topic, how much
effort the reply takes, whether they restart the chat after silence. Every
channel is noisy and any one of them can lie.

DELIBERATE CONFOUNDS
--------------------
These exist so the model cannot pass by memorising a single cue - each one is a
real pattern that the old template model got backwards:

* ``busy_but_interested``  - slow replies, high substance. Latency alone is a trap.
* ``polite_disinterest``   - long, warm, grammatical replies that never ask
                             anything back and never initiate. Length is a trap.
* ``dry_texter_interested``- "ok", "haan", "sure" - but instantly, always, and
                             they start the conversation. Brevity is a trap.
* ``emoji_habit_low_interest`` - a lone 😂 and nothing else. Emoji are a trap.
* ``formal_high_interest`` - no emoji, no "yesss", full punctuation, deeply
                             engaged. Enthusiasm markers are a trap.

Labels come from the latent interest at that point in the conversation, blurred
at the bucket boundaries, so the Bayes error is non-zero and reported accuracy
means something.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

__all__ = [
    'Persona', 'Conversation', 'CorpusGenerator',
    'REGISTERS', 'SCENARIOS', 'INTEREST_ARCS',
]


# ---------------------------------------------------------------------------
# Surface language banks
# ---------------------------------------------------------------------------

TOPICS: Dict[str, Dict[str, List[str]]] = {
    'work': {
        'nouns': ['deadline', 'standup', 'manager', 'appraisal', 'client call', 'presentation'],
        'verbs': ['finished', 'postponed', 'messed up', 'nailed', 'survived'],
    },
    'food': {
        'nouns': ['biryani', 'ramen', 'that new cafe', 'street tacos', 'cold coffee', 'paneer roll'],
        'verbs': ['tried', 'ordered', 'cooked', 'burnt', 'demolished'],
    },
    'travel': {
        'nouns': ['Goa', 'Manali', 'the hill station trip', 'Bangkok', 'the road trip', 'Kerala'],
        'verbs': ['booked', 'cancelled', 'planned', 'got back from'],
    },
    'movies': {
        'nouns': ['that thriller', 'the new Marvel one', 'a documentary', 'the finale', 'that Korean series'],
        'verbs': ['watched', 'binged', 'started', 'gave up on'],
    },
    'gym': {
        'nouns': ['leg day', 'the 5k', 'my trainer', 'protein shakes', 'the morning run'],
        'verbs': ['skipped', 'crushed', 'started', 'regretted'],
    },
    'exams': {
        'nouns': ['the semester exam', 'that assignment', 'my project viva', 'the entrance test'],
        'verbs': ['bombed', 'cleared', 'crammed for', 'postponed'],
    },
    'family': {
        'nouns': ['my cousin\'s wedding', 'my mom', 'the family dinner', 'my brother'],
        'verbs': ['visited', 'argued with', 'surprised', 'called'],
    },
    'music': {
        'nouns': ['that album', 'the concert', 'this playlist', 'their new single'],
        'verbs': ['discovered', 'looped', 'got tickets for', 'skipped'],
    },
    'gaming': {
        'nouns': ['the ranked grind', 'that boss fight', 'the new patch', 'valorant'],
        'verbs': ['lost at', 'finally beat', 'uninstalled', 'got hooked on'],
    },
    'plans': {
        'nouns': ['Saturday', 'the meetup', 'coffee', 'that plan we made', 'dinner'],
        'verbs': ['is on for', 'need to reschedule', 'am free on', 'forgot about'],
    },
}

# Registers describe *how* somebody types, independent of how much they like you.
REGISTERS: Dict[str, Dict[str, Any]] = {
    'english': {
        'fillers': ['honestly', 'i mean', 'tbh', 'you know', 'ngl'],
        'agree': ['yeah', 'right', 'exactly', 'true', 'for sure'],
        'dry': ['ok', 'okay', 'hmm', 'k', 'sure', 'yeah', 'cool', 'fine', 'right'],
        'ack': ['oh nice', 'that\'s cool', 'oh okay', 'makes sense', 'i see', 'ah got it'],
        'warm': ['that sounds amazing', 'i love that', 'that\'s so good', 'wait that\'s great'],
        'laugh': ['haha', 'hahaha', 'lol', 'lmao', 'hahahaha'],
        'emoji': ['😊', '😂', '❤️', '😍', '🙌', '✨', '🥰', '😅', '👀'],
        'lengthen': True,
    },
    'hinglish': {
        'fillers': ['yaar', 'matlab', 'arre', 'bhai', 'na'],
        'agree': ['haan', 'bilkul', 'sahi hai', 'exactly', 'haan yaar'],
        'dry': ['haan', 'hmm', 'achha', 'ok', 'theek hai', 'accha', 'k'],
        'ack': ['achha okay', 'haan samajh gaya', 'oh nice yaar', 'accha accha'],
        'warm': ['arre wah', 'that\'s so good yaar', 'bahut badhiya', 'mast hai'],
        'laugh': ['hahaha', 'lol', 'hahahaha', 'lmaoo'],
        'emoji': ['😂', '❤️', '🙏', '😍', '🤣', '😅', '🥺'],
        'lengthen': True,
    },
    'genz': {
        'fillers': ['fr', 'ngl', 'lowkey', 'istg', 'deadass', 'no cap'],
        'agree': ['fr', 'facts', 'real', 'exactly this', 'yesss'],
        'dry': ['k', 'ok', 'mm', 'word', 'aight', 'sure'],
        'ack': ['oh word', 'ohh okay', 'thats cool', 'ah i see'],
        'warm': ['okay this is actually so good', 'im obsessed', 'this is sending me', 'wait thats fire'],
        # 😭 and 💀 read as laughter here, not sadness - a distinction the old
        # emoji taxonomy gets exactly backwards.
        'laugh': ['💀', '😭', 'lmaooo', 'im crying', 'HELP', 'sobbing'],
        'emoji': ['💀', '😭', '✨', '🫶', '😩', '🥲', '🔥', '👀', '😌'],
        'lengthen': True,
    },
    'formal': {
        'fillers': ['actually', 'to be fair', 'in any case', 'that said'],
        'agree': ['agreed', 'that makes sense', 'quite right', 'indeed'],
        'dry': ['Okay.', 'Understood.', 'Noted.', 'Alright.', 'Sure.'],
        'ack': ['That sounds good.', 'Understood, thanks.', 'Good to know.'],
        'warm': ['That sounds genuinely wonderful.', 'I am really glad to hear that.',
                 'That is excellent news.'],
        'laugh': ['Haha', 'That is funny', 'Ha'],
        'emoji': ['🙂'],
        'lengthen': False,   # never types "yesss" or "okayyy"
    },
}

# Chat artefacts that show up in every real export and never in synthetic data.
ARTEFACTS = [
    '<Media omitted>', 'image omitted', 'sticker omitted', 'audio omitted',
    'This message was deleted', 'video omitted',
]

LINKS = [
    'https://youtu.be/dQw4w9WgXcQ',
    'https://instagram.com/p/CxYz123/',
    'https://open.spotify.com/track/4uLU6hMCjMI75M1A2tKUQC',
    'https://maps.app.goo.gl/xyz123',
]

DEFLECTIONS = {
    'english': ['in a meeting, ttyl', 'busy rn', 'can\'t talk now', 'at work sorry', 'brb'],
    'hinglish': ['abhi busy hoon', 'baad me baat karte hain', 'ghar pe guests hain', 'class me hoon'],
    'genz': ['cant rn sry', 'busy ttyl', 'in class', 'brb dinner'],
    'formal': ['I am in a meeting, will revert shortly.', 'Apologies, tied up at the moment.'],
}

APOLOGIES = {
    'english': ['sorry just saw this', 'sorry was swamped today', 'ugh sorry my phone died'],
    'hinglish': ['sorry yaar abhi dekha', 'sorry, kaam me phas gaya tha'],
    'genz': ['sry just saw this', 'omg sorry my phone was dead'],
    'formal': ['Apologies for the delayed reply.', 'Sorry, I only just saw this.'],
}

TYPO_SWAPS = [
    ('the', 'teh'), ('what', 'waht'), ('that', 'taht'), ('you', 'yuo'),
    ('and', 'adn'), ('just', 'jsut'), ('really', 'realy'), ('with', 'wiht'),
]

SENDER_NAMES = [
    'Aarav', 'Maya', 'Rohan', 'Ananya', 'Sarah', 'John', 'Ishaan', 'Priya',
    'Alex', 'Emma', 'Kabir', 'Diya', 'Zoya', 'Vikram', 'Nikhil', 'Tara',
    'Mom', 'Sam', '+91 98765 43210', 'Riya ✨', 'Dev',
]


# ---------------------------------------------------------------------------
# Personas, scenarios, arcs
# ---------------------------------------------------------------------------

@dataclass
class Persona:
    """How somebody texts, separately from how much they care."""
    name: str
    register: str
    verbosity: float          # baseline words per reply
    emoji_affinity: float     # 0 = never uses emoji, 1 = every message
    latency_base_min: float   # baseline minutes to reply to anyone
    latency_spread: float     # log-normal sigma; high = erratic
    typo_rate: float
    question_habit: float     # baseline tendency to ask things
    availability: str         # 'always_on' | 'business_hours' | 'evenings' | 'erratic'
    lengthen_words: bool = True   # "yesss", "okayyy"
    caps_habit: float = 0.05

    @staticmethod
    def sample(rng: random.Random, register: Optional[str] = None,
               **overrides) -> 'Persona':
        register = register or rng.choice(list(REGISTERS))
        persona = Persona(
            name=rng.choice(SENDER_NAMES),
            register=register,
            verbosity=rng.uniform(2.0, 16.0),
            emoji_affinity=rng.random() ** 1.5,
            latency_base_min=round(10 ** rng.uniform(-0.5, 2.4), 1),  # 0.3 min .. 4 h
            latency_spread=rng.uniform(0.6, 1.9),
            typo_rate=rng.uniform(0.0, 0.14),
            question_habit=rng.uniform(0.05, 0.5),
            availability=rng.choice(
                ['always_on', 'business_hours', 'evenings', 'erratic']
            ),
            lengthen_words=REGISTERS[register]['lengthen'],
            caps_habit=rng.uniform(0.0, 0.25),
        )
        if register == 'formal':
            persona.emoji_affinity = min(persona.emoji_affinity, 0.12)
            persona.typo_rate = min(persona.typo_rate, 0.02)
        for key, value in overrides.items():
            setattr(persona, key, value)
        return persona


# Scenarios pin the persona knobs that create the confounds. `interest` is the
# band the latent interest is drawn from - the label source.
SCENARIOS: Dict[str, Dict[str, Any]] = {
    'new_match_keen': {
        'interest': (0.72, 1.0),
        'persona': {'latency_base_min': (0.3, 6), 'question_habit': (0.35, 0.6)},
        'arc': ['steady', 'warming'],
    },
    'new_match_fading': {
        'interest': (0.30, 0.62),
        'persona': {'latency_base_min': (5, 120)},
        'arc': ['cooling', 'spike_then_fade'],
    },
    'close_friend_banter': {
        'interest': (0.62, 0.95),
        'persona': {'verbosity': (2, 8), 'question_habit': (0.2, 0.45)},
        'arc': ['steady'],
    },
    'late_night_deep_talk': {
        'interest': (0.68, 1.0),
        'persona': {'verbosity': (10, 22), 'availability': 'always_on'},
        'arc': ['warming', 'steady'],
        'start_hour': (22, 26),
    },
    'work_colleague': {
        'interest': (0.34, 0.60),
        'persona': {'register': 'formal', 'availability': 'business_hours',
                    'emoji_affinity': (0.0, 0.08), 'question_habit': (0.1, 0.3)},
        'arc': ['steady'],
    },
    'logistics_only': {
        'interest': (0.30, 0.55),
        'persona': {'verbosity': (3, 9), 'question_habit': (0.15, 0.4)},
        'arc': ['steady'],
    },
    'ghosting': {
        'interest': (0.02, 0.22),
        'persona': {'latency_base_min': (60, 900), 'question_habit': (0.0, 0.08)},
        'arc': ['cooling'],
    },
    'one_sided_pursuit': {
        'interest': (0.04, 0.28),
        'persona': {'verbosity': (1, 4), 'question_habit': (0.0, 0.06),
                    'latency_base_min': (30, 600)},
        'arc': ['cooling', 'steady'],
    },
    'warming_up_stranger': {
        'interest': (0.35, 0.85),
        'persona': {'question_habit': (0.1, 0.4)},
        'arc': ['warming'],
    },
    'long_distance_friend': {
        'interest': (0.60, 0.92),
        'persona': {'latency_base_min': (120, 900), 'verbosity': (12, 25),
                    'availability': 'erratic'},
        'arc': ['steady', 'revival'],
    },
    # --- the confounds -----------------------------------------------------
    'busy_but_interested': {
        'interest': (0.66, 0.95),
        'persona': {'latency_base_min': (90, 600), 'verbosity': (10, 20),
                    'question_habit': (0.35, 0.6), 'availability': 'business_hours'},
        'arc': ['steady'],
        'apologise_for_delay': 0.55,
    },
    'polite_disinterest': {
        'interest': (0.12, 0.34),
        'persona': {'verbosity': (12, 24), 'question_habit': (0.0, 0.04),
                    'register': 'formal', 'latency_base_min': (20, 240)},
        'arc': ['steady', 'cooling'],
        # Long, courteous replies without genuine initiative: a deliberate
        # confound for models that equate word count with interest.
        'polite_warm': True,
    },
    'dry_texter_interested': {
        'interest': (0.66, 0.95),
        'persona': {'verbosity': (1.0, 3.5), 'emoji_affinity': (0.0, 0.1),
                    'latency_base_min': (0.2, 2.5), 'question_habit': (0.3, 0.55),
                    'availability': 'always_on'},
        'arc': ['steady'],
        # Short replies despite genuine interest: brevity is a deliberate
        # confound rather than a label shortcut.
        'dry_interested': True,
    },
    'emoji_habit_low_interest': {
        'interest': (0.08, 0.32),
        'persona': {'emoji_affinity': (0.75, 1.0), 'verbosity': (1, 3),
                    'question_habit': (0.0, 0.05)},
        'arc': ['steady', 'cooling'],
    },
    'formal_high_interest': {
        'interest': (0.70, 0.97),
        'persona': {'register': 'formal', 'emoji_affinity': (0.0, 0.05),
                    'verbosity': (14, 26), 'question_habit': (0.4, 0.65)},
        'arc': ['steady', 'warming'],
    },
}

INTEREST_ARCS = ['steady', 'warming', 'cooling', 'spike_then_fade', 'revival']


def _arc_value(arc: str, position: float, base: float, rng: random.Random) -> float:
    """
    Latent interest at `position` (0..1 through the conversation).

    Kept gentle - real feelings drift over a chat, they do not switch. The small
    jitter is genuine turn-to-turn variation, not label noise.
    """
    jitter = rng.gauss(0, 0.035)

    if arc == 'warming':
        value = base * (0.62 + 0.55 * position)
    elif arc == 'cooling':
        value = base * (1.08 - 0.6 * position)
    elif arc == 'spike_then_fade':
        value = base * (0.8 + 0.7 * (1 - abs(position - 0.3) / 0.7))
    elif arc == 'revival':
        value = base * (1.0 - 0.55 * position + 0.75 * max(0.0, position - 0.7))
    else:
        value = base

    return min(1.0, max(0.0, value + jitter))


# ---------------------------------------------------------------------------
# Reply modes - how interest turns into behaviour
# ---------------------------------------------------------------------------

# Mode weights at interest 0 and interest 1; interpolated in between. This is
# the actual model of engagement: interested people elaborate and ask back,
# uninterested people acknowledge and deflect.
MODE_WEIGHTS: Dict[str, Tuple[float, float]] = {
    'dry':        (0.46, 0.04),
    'ack':        (0.24, 0.07),
    'deflect':    (0.14, 0.02),
    'engage':     (0.09, 0.24),
    'elaborate':  (0.03, 0.26),
    'enthuse':    (0.01, 0.19),
    'ask_back':   (0.02, 0.16),
    'artefact':   (0.01, 0.02),
}


def _mode_for(interest: float, persona: Persona, rng: random.Random) -> str:
    weights = []
    modes = []
    for mode, (low, high) in MODE_WEIGHTS.items():
        weight = low + (high - low) * interest
        # A naturally inquisitive person asks things even when lukewarm, and a
        # terse person stays terse even when smitten.
        if mode == 'ask_back':
            weight *= 0.5 + 2.0 * persona.question_habit
        if mode in ('elaborate', 'enthuse'):
            weight *= 0.4 + persona.verbosity / 12.0
        if mode == 'dry':
            weight *= 1.6 - min(persona.verbosity, 18) / 18.0
        modes.append(mode)
        weights.append(max(weight, 1e-4))
    return rng.choices(modes, weights=weights, k=1)[0]


# ---------------------------------------------------------------------------
# Conversation container
# ---------------------------------------------------------------------------

@dataclass
class Conversation:
    messages: List[Dict[str, Any]]        # sender, message, datetime, timestamp
    pair_labels: List[Tuple[int, int, int]]  # (your_index, their_index, label 0-4)
    scenario: str
    arc: str
    user: str
    other: str
    meta: Dict[str, Any] = field(default_factory=dict)

    def to_whatsapp_export(self, seconds: bool = True) -> str:
        """Render as a WhatsApp .txt export, the format users actually upload."""
        lines = []
        for msg in self.messages:
            stamp = msg['datetime']
            fmt = '%d/%m/%Y, %H:%M:%S' if seconds else '%d/%m/%Y, %H:%M'
            lines.append(f"{stamp.strftime(fmt)} - {msg['sender']}: {msg['message']}")
        return "\n".join(lines)

    def to_bracket_export(self) -> str:
        """`[DD/MM/YYYY, HH:MM:SS] Sender: message` - the other common shape."""
        return "\n".join(
            f"[{m['datetime'].strftime('%d/%m/%Y, %H:%M:%S')}] {m['sender']}: {m['message']}"
            for m in self.messages
        )

    def to_json_export(self) -> List[Dict[str, str]]:
        return [
            {
                'sender': m['sender'],
                'message': m['message'],
                'timestamp': m['datetime'].isoformat(),
            }
            for m in self.messages
        ]


# ---------------------------------------------------------------------------
# Generator
# ---------------------------------------------------------------------------

class CorpusGenerator:
    """
    Produces labelled conversations that behave like real chats.

    Args:
        seed: RNG seed. Train/val/test use disjoint seeds.
        scenarios: restrict to a subset of scenario names. Used to hold entire
            scenarios out of training so the test split measures generalisation
            to relationship dynamics the model has never seen.
    """

    def __init__(self, seed: int = 0, scenarios: Optional[List[str]] = None):
        self.rng = random.Random(seed)
        self.scenario_names = list(scenarios) if scenarios else list(SCENARIOS)

    # --- public -----------------------------------------------------------

    def generate(self, count: int) -> List[Conversation]:
        return [self.generate_one() for _ in range(count)]

    def generate_one(self, scenario: Optional[str] = None) -> Conversation:
        rng = self.rng
        scenario = scenario or rng.choice(self.scenario_names)
        spec = SCENARIOS[scenario]

        other = self._persona_for(spec)
        user = Persona.sample(rng)   # you text how you text, regardless

        low, high = spec['interest']
        base_interest = rng.uniform(low, high)
        arc = rng.choice(spec.get('arc', INTEREST_ARCS))

        turns = rng.randint(5, 26)          # exchanges, so ~10-52 messages
        clock = self._start_time(spec)

        messages: List[Dict[str, Any]] = []
        pair_labels: List[Tuple[int, int, int]] = []
        topic = rng.choice(list(TOPICS))

        for turn in range(turns):
            position = turn / max(turns - 1, 1)
            interest = _arc_value(arc, position, base_interest, rng)

            # Occasionally you switch topic mid-chat, like people do.
            if rng.random() < 0.22:
                topic = rng.choice(list(TOPICS))

            # --- your message(s) --------------------------------------------
            clock = self._advance(clock, self._latency(user, 0.6, rng), user)
            your_index = len(messages)
            messages.append(self._message(
                user, self._compose_user_message(user, topic, turn, rng), clock
            ))

            # Double-texting: common, and much more common when they are not
            # replying much.
            if rng.random() < 0.10 + 0.28 * (1 - interest):
                clock = self._advance(clock, rng.uniform(1, 25), user)
                messages.append(self._message(
                    user, self._compose_user_message(user, topic, turn, rng), clock
                ))
                your_index = len(messages) - 1

            # --- their reply, or silence ------------------------------------
            # Low interest does not just reply badly; sometimes it does not
            # reply at all. Those unanswered messages are a real signal, and
            # they produce no pair.
            if rng.random() < 0.30 * (1 - interest) ** 2:
                continue

            delay = self._latency(other, interest, rng)
            clock = self._advance(clock, delay, other)
            their_index = len(messages)
            reply = self._compose_reply(
                other, interest, messages[your_index]['message'], topic,
                delay, spec, rng
            )
            messages.append(self._message(other, reply, clock))

            pair_labels.append((your_index, their_index, self._label(interest, rng)))

            # A keen person often follows up their own reply.
            if rng.random() < 0.05 + 0.22 * interest:
                clock = self._advance(clock, rng.uniform(0.2, 3), other)
                messages.append(self._message(
                    other,
                    self._compose_reply(other, interest,
                                        messages[your_index]['message'], topic,
                                        0.5, spec, rng),
                    clock
                ))

        return Conversation(
            messages=messages,
            pair_labels=pair_labels,
            scenario=scenario,
            arc=arc,
            user=user.name,
            other=other.name,
            meta={
                'base_interest': round(base_interest, 3),
                'other_register': other.register,
                'other_latency_base_min': other.latency_base_min,
                'other_emoji_affinity': round(other.emoji_affinity, 2),
                'other_verbosity': round(other.verbosity, 1),
            },
        )

    # --- persona / label --------------------------------------------------

    def _persona_for(self, spec: Dict[str, Any]) -> Persona:
        rng = self.rng
        knobs = dict(spec.get('persona', {}))
        register = knobs.pop('register', None)
        persona = Persona.sample(rng, register=register)

        for key, value in knobs.items():
            if isinstance(value, tuple):
                setattr(persona, key, rng.uniform(*value))
            else:
                setattr(persona, key, value)

        persona.lengthen_words = REGISTERS[persona.register]['lengthen']
        return persona

    @staticmethod
    def _label(interest: float, rng: random.Random) -> int:
        """
        Bucket latent interest into the five reported bands.

        The boundary blur matters: somebody at 0.595 and somebody at 0.605 are
        indistinguishable in practice, so forcing a crisp split would teach the
        model a precision that does not exist and inflate its scores.
        """
        blurred = interest + rng.gauss(0, 0.05)
        return int(min(4, max(0, blurred * 5)))

    # --- timing -----------------------------------------------------------

    def _start_time(self, spec: Dict[str, Any]) -> datetime:
        rng = self.rng
        start = datetime(2024, 1, 1) + timedelta(
            days=rng.randint(0, 700), minutes=rng.randint(0, 1440)
        )
        window = spec.get('start_hour')
        if window:
            hour = rng.randint(*window) % 24
            start = start.replace(hour=hour, minute=rng.randint(0, 59))
        return start.replace(second=rng.randint(0, 59), microsecond=0)

    @staticmethod
    def _latency(persona: Persona, interest: float, rng: random.Random) -> float:
        """
        Minutes before this person replies.

        Two multiplicative parts: their own baseline pace (a busy person is slow
        to everyone) and an interest term that can pull it down by ~4x. Plus a
        fat tail, because sometimes a phone is just face-down in another room.
        """
        eagerness = 0.25 + 0.75 * (1.0 - interest) ** 1.4
        delay = persona.latency_base_min * eagerness * rng.lognormvariate(
            0, persona.latency_spread
        )
        if rng.random() < 0.06:                  # phone in another room
            delay *= rng.uniform(6, 40)
        return max(0.1, min(delay, 60 * 72))

    @staticmethod
    def _advance(clock: datetime, minutes: float, persona: Persona) -> datetime:
        """
        Move the clock forward, then respect when this person is actually
        reachable. This is what produces the overnight and workday gaps that
        dominate real reply-time distributions.
        """
        stamp = clock + timedelta(minutes=minutes)

        for _ in range(4):
            hour = stamp.hour
            if persona.availability == 'always_on':
                if 2 <= hour < 7:                      # even night owls sleep
                    stamp = stamp.replace(hour=7, minute=stamp.minute % 60)
                break
            if persona.availability == 'business_hours':
                if hour < 8:
                    stamp = stamp.replace(hour=8)
                elif hour >= 20:
                    stamp = (stamp + timedelta(days=1)).replace(hour=8)
                elif 9 <= hour < 18 and stamp.minute % 7 == 0:
                    stamp += timedelta(minutes=45)     # stuck in a meeting
                    continue
                break
            if persona.availability == 'evenings':
                if 9 <= hour < 18:
                    stamp = stamp.replace(hour=18, minute=stamp.minute % 60)
                elif hour < 7:
                    stamp = stamp.replace(hour=18)
                break
            # erratic: awake at odd hours, only truly gone in the small hours
            if 3 <= hour < 6:
                stamp = stamp.replace(hour=9)
            break

        return stamp.replace(microsecond=0)

    @staticmethod
    def _message(persona: Persona, text: str, stamp: datetime) -> Dict[str, Any]:
        return {
            'sender': persona.name,
            'message': text,
            'datetime': stamp,
            'timestamp': stamp.strftime('%d/%m/%Y, %H:%M:%S'),
        }

    # --- text composition -------------------------------------------------

    def _compose_user_message(self, persona: Persona, topic: str,
                              turn: int, rng: random.Random) -> str:
        bank = REGISTERS[persona.register]
        noun = rng.choice(TOPICS[topic]['nouns'])
        verb = rng.choice(TOPICS[topic]['verbs'])

        shapes = [
            f"i {verb} {noun} yesterday",
            f"so about {noun}...",
            f"have you {verb} {noun}?",
            f"what do you think about {noun}?",
            f"guess what, i finally {verb} {noun}",
            f"{noun} was honestly something else",
            f"how was your day?",
            f"are you free this weekend?",
            f"you free to talk about {noun}?",
            f"remember {noun}? there's an update",
        ]
        if turn == 0:
            shapes = ['hey', 'hey! how are you?', 'yo', f"hi! quick question about {noun}",
                      'hey, you around?']

        text = rng.choice(shapes)

        if rng.random() < 0.12:
            text += ' ' + rng.choice(LINKS)
        if rng.random() < 0.06:
            text = rng.choice(ARTEFACTS)
        if rng.random() < 0.35:
            text += ' ' + rng.choice(bank['fillers'])

        return self._surface(text, persona, rng)

    def _compose_reply(self, persona: Persona, interest: float,
                       your_message: str, topic: str, delay_min: float,
                       spec: Dict[str, Any], rng: random.Random) -> str:
        bank = REGISTERS[persona.register]
        mode = _mode_for(interest, persona, rng)

        # Keep the two documented confounds behaviourally distinct. The latent
        # label remains unchanged; only surface reply style is controlled here.
        if spec.get('polite_warm'):
            mode = 'elaborate' if rng.random() < 0.78 else 'ack'
        elif spec.get('dry_interested'):
            mode = 'dry' if rng.random() < 0.78 else 'ask_back'

        # Echoing your words back is one of the clearest signs somebody is
        # actually reading you, so topic pickup scales with interest.
        echo = ''
        content = [w for w in your_message.split() if len(w) > 4 and w.isalpha()]
        if content and rng.random() < 0.15 + 0.55 * interest:
            echo = rng.choice(content).lower()

        if mode == 'dry':
            text = rng.choice(bank['dry'])
        elif mode == 'ack':
            text = rng.choice(bank['ack'])
        elif mode == 'deflect':
            text = rng.choice(DEFLECTIONS[persona.register])
        elif mode == 'artefact':
            text = rng.choice(ARTEFACTS)
        elif mode == 'engage':
            noun = echo or rng.choice(TOPICS[topic]['nouns'])
            text = rng.choice([
                f"{rng.choice(bank['agree'])}, {noun} is exactly what i meant",
                f"oh the {noun} part - i was thinking the same",
                f"{rng.choice(bank['agree'])} i've been meaning to try {noun}",
            ])
        elif mode == 'elaborate':
            noun = echo or rng.choice(TOPICS[topic]['nouns'])
            verb = rng.choice(TOPICS[topic]['verbs'])
            text = rng.choice([
                f"okay so i {verb} {noun} last month and it completely changed how i think about it, "
                f"{rng.choice(bank['fillers'])} i still remember the whole thing",
                f"funny you say that, i {verb} {noun} too and honestly the best part was how unexpected it felt",
                f"i have a whole story about {noun}. short version: i {verb} it and immediately regretted every decision",
            ])
        elif mode == 'enthuse':
            text = rng.choice(bank['warm'])
            if rng.random() < 0.6:
                text += ' ' + rng.choice(bank['laugh'])
        else:  # ask_back
            noun = echo or rng.choice(TOPICS[topic]['nouns'])
            text = rng.choice([
                f"wait tell me more about {noun}?",
                f"how did you even get into {noun}?",
                f"what was your favourite part?",
                f"and what about you, how are you holding up?",
                f"do you want to do {noun} together sometime?",
            ])

        # An interested person adds a question on top of whatever they said.
        if mode not in ('ask_back', 'deflect') and \
                rng.random() < persona.question_habit * (0.3 + interest):
            text += ' ' + rng.choice(['what about you?', 'you?', 'how about you?',
                                      'right?', 'have you tried it?'])

        # Apologising for a slow reply is what "busy but interested" looks like.
        if delay_min > 120 and rng.random() < spec.get('apologise_for_delay', 0.12) + 0.2 * interest:
            text = rng.choice(APOLOGIES[persona.register]) + ' ' + text

        return self._surface(text, persona, rng, interest=interest)

    def _surface(self, text: str, persona: Persona, rng: random.Random,
                 interest: float = 0.5) -> str:
        """
        Apply persona-level typing habits. These are *style*, not sentiment -
        which is exactly why the model must not read them as interest on their
        own.
        """
        bank = REGISTERS[persona.register]

        if rng.random() < persona.typo_rate:
            for correct, typo in TYPO_SWAPS:
                if correct in text:
                    text = text.replace(correct, typo, 1)
                    break

        # Stretched words ("yesss") track excitement, but only for people whose
        # register does that at all.
        if persona.lengthen_words and rng.random() < 0.12 + 0.4 * interest:
            words = text.split()
            if words:
                index = rng.randrange(len(words))
                word = words[index]
                if len(word) > 2 and word[-1].isalpha():
                    words[index] = word + word[-1] * rng.randint(1, 3)
                    text = ' '.join(words)

        if rng.random() < persona.caps_habit:
            words = text.split()
            if words:
                index = rng.randrange(len(words))
                if len(words[index]) > 2:
                    words[index] = words[index].upper()
                    text = ' '.join(words)

        # Emoji count is habit x mood, so a heavy emoji user still peppers a
        # bored "k 😂" and a formal texter stays bare while deeply invested.
        emoji_chance = persona.emoji_affinity * (0.35 + 0.65 * interest)
        if rng.random() < emoji_chance:
            count = 1 if interest < 0.6 else rng.randint(1, 3)
            text += ' ' + ' '.join(rng.choice(bank['emoji']) for _ in range(count))

        if rng.random() < 0.15 + 0.5 * interest:
            if persona.register == 'formal':
                if not text.endswith(('.', '!', '?')):
                    text += '.'
            elif not text.endswith(('!', '?')):
                text = text.rstrip('.') + '!' * rng.randint(1, 3)

        # Real chat is mostly lowercase, except from people who type properly.
        if persona.register != 'formal' and rng.random() < 0.75:
            text = text[0].lower() + text[1:] if text else text

        return text.strip()
