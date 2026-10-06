"""
Conversation timing and flow context.

The interest model used to fill eight of its features with literal constants
(``0.5, 0.7, 0.6, 0.8, 1, 0, 0.5, 0.3``) marked "placeholder for now". In real
life those are the *strongest* signals available: how fast somebody replies, at
what hour, whether they engage with what you actually said, and whether their
attention is steady or erratic. This module computes them for real from the
decoded messages.

Two things matter for honesty here:

* **Absolute vs relative latency.** A 40-minute reply means something very
  different from someone who always takes 40 minutes than from someone who
  usually answers in 30 seconds. Both are exposed so the model can separate a
  busy person from a cooling one.
* **Graceful absence.** Plenty of uploads have no usable timestamps. Rather than
  inventing numbers, the context reports ``available = False``, the timing slots
  fall back to neutral values, and a dedicated flag feature lets the model learn
  to discount them.
"""

from __future__ import annotations

import re
from datetime import datetime
from typing import Any, Dict, List, Optional

import numpy as np

__all__ = ['TIMING_FEATURE_COUNT', 'NEUTRAL_TIMING', 'ConversationContext']

# response_speed_abs, response_speed_rel, continuity, topic_maintenance,
# engagement_consistency, is_daytime, is_late_night, position, available
TIMING_FEATURE_COUNT = 9

# What to feed the model when a conversation carries no usable timestamps:
# mid-scale for the graded signals, and 0.0 in the final slot to say so.
NEUTRAL_TIMING = (0.5, 0.5, 0.5, 0.0, 0.5, 1.0, 0.0, 0.5, 0.0)

# Latency at which the absolute-speed score decays to 1/e. Chosen so that a
# reply inside a couple of minutes reads as eager, half an hour is middling and
# several hours is cold - which is how chat actually feels.
_SPEED_HALFLIFE_MIN = 45.0

# Same-session window. Beyond this the exchange is a new sitting, not a volley.
_SESSION_GAP_MIN = 30.0

_STOPWORDS = {
    'about', 'after', 'again', 'also', 'been', 'because', 'before', 'being',
    'could', 'dont', "don't", 'even', 'ever', 'from', 'have', 'here', 'just',
    'know', 'like', 'more', 'much', 'only', 'other', 'over', 'really', 'said',
    'same', 'should', 'some', 'still', 'such', 'than', 'that', 'their', 'them',
    'then', 'there', 'these', 'they', 'thing', 'think', 'this', 'those',
    'through', 'very', 'want', 'well', 'were', 'what', 'when', 'where', 'which',
    'while', 'with', 'would', 'your', 'youre', "you're", 'yeah', 'gonna',
}

_WORD = re.compile(r"[a-z']+")


def _content_words(text: str) -> set:
    """Words that carry topic meaning - long enough, not filler."""
    return {
        w for w in _WORD.findall(text.lower())
        if len(w) > 3 and w not in _STOPWORDS
    }


class ConversationContext:
    """
    Timing and flow context for one conversation.

    Build it once per conversation, then ask it for the context of each
    (your message -> their reply) pair.
    """

    def __init__(self, messages: List[Dict[str, Any]], user: str, other: str):
        self.messages = messages
        self.user = user
        self.other = other
        self.total = max(len(messages), 1)

        self._stamps: List[Optional[datetime]] = [
            self._stamp_of(m) for m in messages
        ]
        self.available = sum(s is not None for s in self._stamps) >= 2

        # Their reply latencies across the whole conversation, so a single pair
        # can be judged against this person's own normal pace.
        self._their_delays = self._collect_reply_delays(other)
        self._your_delays = self._collect_reply_delays(user)

        self._their_median = (
            float(np.median(self._their_delays)) if self._their_delays else None
        )
        self._your_median = (
            float(np.median(self._your_delays)) if self._your_delays else None
        )
        self._consistency = self._latency_consistency(self._their_delays)

    # --- construction helpers ------------------------------------------------

    @staticmethod
    def _stamp_of(message: Dict[str, Any]) -> Optional[datetime]:
        stamp = message.get('datetime')
        if isinstance(stamp, datetime):
            return stamp
        iso = message.get('datetime_iso')
        if isinstance(iso, str):
            try:
                return datetime.fromisoformat(iso.replace('Z', '+00:00')).replace(tzinfo=None)
            except ValueError:
                return None
        return None

    def _collect_reply_delays(self, sender: str) -> List[float]:
        """Minutes `sender` took to answer the *other* participant."""
        delays = []
        for i in range(1, len(self.messages)):
            if self.messages[i].get('sender') != sender:
                continue
            if self.messages[i - 1].get('sender') == sender:
                continue  # consecutive message from the same person, not a reply
            before, after = self._stamps[i - 1], self._stamps[i]
            if before is None or after is None:
                continue
            minutes = (after - before).total_seconds() / 60.0
            if 0 <= minutes <= 60 * 24 * 7:  # ignore nonsense / week-plus gaps
                delays.append(minutes)
        return delays

    @staticmethod
    def _latency_consistency(delays: List[float]) -> float:
        """
        1.0 when somebody answers at a steady pace, falling towards 0 when their
        attention is erratic (instant one moment, hours the next).
        """
        if len(delays) < 3:
            return 0.5
        mean = float(np.mean(delays))
        if mean <= 0:
            return 1.0
        cv = float(np.std(delays)) / mean
        return float(1.0 / (1.0 + cv))

    # --- public API ----------------------------------------------------------

    def pair_context(self, your_index: int, their_index: int) -> Dict[str, float]:
        """
        Context for the pair at (`your_index` -> `their_index`).

        Returns the nine timing values in the order `extract_features` consumes,
        under readable keys. Values are all in 0..1 so they sit comfortably
        alongside the other normalized features.
        """
        your_msg = self.messages[your_index]
        their_msg = self.messages[their_index]

        topic = self._topic_overlap(
            your_msg.get('message', ''), their_msg.get('message', '')
        )

        if not self.available:
            neutral = dict(zip(self.keys(), NEUTRAL_TIMING))
            neutral['topic_maintenance'] = topic  # text-only, always computable
            neutral['position'] = their_index / self.total
            return neutral

        before, after = self._stamps[your_index], self._stamps[their_index]

        if before is None or after is None:
            speed_abs = 0.5
            speed_rel = 0.5
            continuity = 0.5
            hour = None
            has_timing = 0.0
        else:
            delay_min = max((after - before).total_seconds() / 60.0, 0.0)
            speed_abs = float(np.exp(-delay_min / _SPEED_HALFLIFE_MIN))
            speed_rel = self._relative_speed(delay_min)
            continuity = float(np.exp(-delay_min / (_SESSION_GAP_MIN * 2)))
            hour = after.hour
            has_timing = 1.0

        return {
            'response_speed_abs': speed_abs,
            'response_speed_rel': speed_rel,
            'continuity': continuity,
            'topic_maintenance': topic,
            'engagement_consistency': self._consistency,
            'is_daytime': 1.0 if hour is None or 8 <= hour < 20 else 0.0,
            'is_late_night': 1.0 if hour is not None and (hour >= 23 or hour < 5) else 0.0,
            'position': their_index / self.total,
            'timing_available': has_timing,
        }

    @staticmethod
    def keys():
        return (
            'response_speed_abs', 'response_speed_rel', 'continuity',
            'topic_maintenance', 'engagement_consistency', 'is_daytime',
            'is_late_night', 'position', 'timing_available',
        )

    @staticmethod
    def as_vector(context: Optional[Dict[str, float]]) -> List[float]:
        """Flatten a pair context into the nine feature slots, in order."""
        if not context:
            return list(NEUTRAL_TIMING)
        return [float(context.get(k, d))
                for k, d in zip(ConversationContext.keys(), NEUTRAL_TIMING)]

    def _relative_speed(self, delay_min: float) -> float:
        """
        Their latency against their own median: 0.5 means "their usual pace",
        above means faster than usual (leaning in), below means slower (drifting).
        """
        median = self._their_median
        if not median or median <= 0:
            return 0.5
        return float(median / (median + max(delay_min, 0.0)))

    @staticmethod
    def _topic_overlap(your_text: str, their_text: str) -> float:
        """
        Do they actually pick up what you said? Jaccard over content words.
        A reply that reuses your nouns is engaging with you; "ok" is not.
        """
        yours, theirs = _content_words(your_text), _content_words(their_text)
        if not yours or not theirs:
            return 0.0
        return len(yours & theirs) / len(yours | theirs)

    # --- conversation-level summary -----------------------------------------

    def timing_summary(self) -> Dict[str, Any]:
        """
        Human-readable timing stats for the analysis report. These are the
        numbers people actually recognise from their own chats.
        """
        summary: Dict[str, Any] = {
            'timing_available': self.available,
            'their_median_reply_minutes': (
                round(self._their_median, 1) if self._their_median is not None else None
            ),
            'your_median_reply_minutes': (
                round(self._your_median, 1) if self._your_median is not None else None
            ),
            'reply_speed_consistency': round(self._consistency, 2),
        }

        if self._their_median is not None and self._your_median is not None:
            # >1 means they make you wait longer than you make them wait.
            summary['reply_delay_ratio'] = round(
                self._their_median / max(self._your_median, 0.1), 2
            )

        summary.update(self._initiation_stats())
        summary['interpretation'] = self._interpret_timing(summary)
        return summary

    def _initiation_stats(self) -> Dict[str, Any]:
        """
        Who restarts the chat after it goes quiet? Real-life interest shows up
        far more in who reaches out first than in what they type.
        """
        gap_hours = 6.0
        their_revivals = 0
        your_revivals = 0

        for i in range(1, len(self.messages)):
            before, after = self._stamps[i - 1], self._stamps[i]
            if before is None or after is None:
                continue
            if (after - before).total_seconds() / 3600.0 < gap_hours:
                continue
            sender = self.messages[i].get('sender')
            if sender == self.other:
                their_revivals += 1
            elif sender == self.user:
                your_revivals += 1

        total = their_revivals + your_revivals
        return {
            'they_restarted_chat': their_revivals,
            'you_restarted_chat': your_revivals,
            'their_initiation_share': (
                round(their_revivals / total * 100, 1) if total else None
            ),
        }

    @staticmethod
    def _interpret_timing(summary: Dict[str, Any]) -> str:
        if not summary.get('timing_available'):
            return "No timestamps in this export, so reply timing could not be measured."

        median = summary.get('their_median_reply_minutes')
        parts = []

        if median is not None:
            if median < 2:
                parts.append("They reply almost instantly")
            elif median < 15:
                parts.append(f"They usually reply within {median:.0f} minutes")
            elif median < 90:
                parts.append(f"They take about {median:.0f} minutes to reply")
            else:
                parts.append(f"They take around {median / 60:.1f} hours to reply")

        ratio = summary.get('reply_delay_ratio')
        if ratio is not None:
            if ratio > 2.5:
                parts.append("noticeably slower than you reply to them")
            elif ratio < 0.4:
                parts.append("faster than you reply to them")
            else:
                parts.append("at a pace close to yours")

        share = summary.get('their_initiation_share')
        if share is not None:
            if share >= 60:
                parts.append("and they are usually the one to restart the chat")
            elif share <= 20:
                parts.append("and you are almost always the one restarting the chat")

        return ", ".join(parts) + "." if parts else "Reply timing looks unremarkable."
