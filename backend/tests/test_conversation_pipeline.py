# -*- coding: utf-8 -*-
"""
Tests for the conversation analysis pipeline.

Covers the three things that had no coverage and were silently wrong:
timestamp parsing across export formats, the timing/flow features that used to
be hard-coded constants, and the decoder round trip the training script relies
on for train/serve parity.

Run with:
    python tests/test_conversation_pipeline.py
    python -m pytest tests/test_conversation_pipeline.py
"""

from __future__ import annotations

import json
import os
import sys
import tempfile
from datetime import datetime, timedelta

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from api.conversation_decoder import ConversationDecoder            # noqa: E402
from api.timestamp_parser import infer_date_order, parse_timestamp   # noqa: E402
from ml_models.conversation_context import ConversationContext       # noqa: E402
from ml_models.conversation_interest_model import (                  # noqa: E402
    FEATURE_DIM,
    ConversationAnalysisService,
)


# --- timestamp parsing ------------------------------------------------------

def test_whatsapp_24h():
    assert parse_timestamp('15/01/2024, 10:30:00') == datetime(2024, 1, 15, 10, 30)


def test_whatsapp_12h_pm():
    assert parse_timestamp('15/01/2024, 10:30 PM') == datetime(2024, 1, 15, 22, 30)


def test_midnight_12am_is_hour_zero():
    assert parse_timestamp('15/01/2024, 12:15 AM') == datetime(2024, 1, 15, 0, 15)


def test_noon_12pm_stays_twelve():
    assert parse_timestamp('15/01/2024, 12:15 PM') == datetime(2024, 1, 15, 12, 15)


def test_two_digit_year():
    assert parse_timestamp('15/01/24, 08:05') == datetime(2024, 1, 15, 8, 5)


def test_iso_timestamp():
    assert parse_timestamp('2024-01-15T14:30:00Z') == datetime(2024, 1, 15, 14, 30)


def test_epoch_seconds_and_millis_agree():
    seconds = parse_timestamp(1705329000)
    millis = parse_timestamp(1705329000000)
    assert seconds is not None and seconds == millis


def test_month_first_detected():
    # 01/15 can only be month-first: there is no 15th month.
    order = infer_date_order(['01/15/2024, 10:00', '02/20/2024, 11:00'])
    assert order == 'month_first'
    assert parse_timestamp('01/15/2024, 10:00', order) == datetime(2024, 1, 15, 10, 0)


def test_day_first_detected():
    order = infer_date_order(['15/01/2024, 10:00', '20/02/2024, 11:00'])
    assert order == 'day_first'
    assert parse_timestamp('15/01/2024, 10:00', order) == datetime(2024, 1, 15, 10, 0)


def test_time_only_rolls_over_midnight():
    previous = datetime(2024, 1, 15, 23, 50)
    # 00:10 after 23:50 is the next day, not eighteen hours earlier.
    assert parse_timestamp('00:10', 'day_first', previous) == datetime(2024, 1, 16, 0, 10)


def test_unparseable_returns_none():
    assert parse_timestamp('not a timestamp') is None
    assert parse_timestamp(None) is None


# --- decoder ---------------------------------------------------------------

def _decode(text: str, suffix: str = '.txt'):
    handle = tempfile.NamedTemporaryFile('w', suffix=suffix, delete=False, encoding='utf-8')
    try:
        handle.write(text)
        handle.close()
        return ConversationDecoder().decode_file(handle.name)
    finally:
        os.unlink(handle.name)


def test_decoder_attaches_datetimes():
    decoded = _decode(
        "15/01/2024, 10:30:00 - Aarav: hey\n"
        "15/01/2024, 10:31:00 - Maya: hey you!\n"
    )
    assert decoded['metadata']['has_timing'] is True
    assert decoded['metadata']['timestamps_parsed'] == 2
    assert decoded['messages'][0]['datetime'] == datetime(2024, 1, 15, 10, 30)
    assert decoded['messages'][1]['datetime_iso'] == '2024-01-15T10:31:00'


def test_decoder_reports_duration():
    decoded = _decode(
        "15/01/2024, 10:00:00 - A: one\n"
        "15/01/2024, 12:00:00 - B: two\n"
    )
    assert decoded['metadata']['duration_hours'] == 2.0


def test_decoder_without_timestamps_flags_no_timing():
    decoded = _decode("Aarav: hey there\nMaya: hello!\n")
    assert decoded['metadata']['has_timing'] is False
    assert decoded['messages'][0]['datetime'] is None


def test_json_export_round_trip():
    payload = json.dumps([
        {'sender': 'Emma', 'message': 'hey!', 'timestamp': '2024-01-15T14:30:00Z'},
        {'sender': 'Alex', 'message': 'hi you', 'timestamp': '2024-01-15T14:32:00Z'},
    ])
    decoded = _decode(payload, suffix='.json')
    assert len(decoded['messages']) == 2
    assert decoded['messages'][1]['datetime'] == datetime(2024, 1, 15, 14, 32)


# --- timing context --------------------------------------------------------

def _chat(delays_min, sender_a='A', sender_b='B'):
    """Build a two-person chat where B replies after each given delay."""
    clock = datetime(2024, 1, 15, 10, 0, 0)
    messages = []
    for delay in delays_min:
        messages.append({'sender': sender_a, 'message': 'what do you think about the trip?',
                         'datetime': clock})
        clock = clock + timedelta(minutes=delay)
        messages.append({'sender': sender_b, 'message': 'the trip sounds great honestly',
                         'datetime': clock})
        clock = clock + timedelta(minutes=5)
    return messages


def test_fast_replies_score_higher_than_slow():
    fast = ConversationContext(_chat([1, 1, 1, 1]), 'A', 'B')
    slow = ConversationContext(_chat([600, 600, 600, 600]), 'A', 'B')

    fast_speed = fast.pair_context(0, 1)['response_speed_abs']
    slow_speed = slow.pair_context(0, 1)['response_speed_abs']
    assert fast_speed > slow_speed
    assert fast_speed > 0.9 and slow_speed < 0.1


def test_relative_speed_is_about_personal_baseline():
    """A slow-but-consistent replier is not penalised on the relative channel."""
    slow = ConversationContext(_chat([600, 600, 600, 600]), 'A', 'B')
    context = slow.pair_context(0, 1)
    # Absolute speed is near zero, but relative to their own median it is normal.
    assert context['response_speed_abs'] < 0.1
    assert 0.4 < context['response_speed_rel'] < 0.6


def test_erratic_replier_scores_lower_consistency():
    steady = ConversationContext(_chat([10, 10, 10, 10, 10]), 'A', 'B')
    erratic = ConversationContext(_chat([1, 600, 2, 900, 3]), 'A', 'B')
    assert (steady.pair_context(0, 1)['engagement_consistency'] >
            erratic.pair_context(0, 1)['engagement_consistency'])


def test_topic_overlap_rewards_engaging_with_content():
    messages = [
        {'sender': 'A', 'message': 'i finally booked the Manali trip for December',
         'datetime': datetime(2024, 1, 15, 10, 0)},
        {'sender': 'B', 'message': 'wait you booked Manali? December is perfect there',
         'datetime': datetime(2024, 1, 15, 10, 1)},
        {'sender': 'A', 'message': 'i finally booked the Manali trip for December',
         'datetime': datetime(2024, 1, 15, 10, 5)},
        {'sender': 'B', 'message': 'k', 'datetime': datetime(2024, 1, 15, 10, 6)},
    ]
    flow = ConversationContext(messages, 'A', 'B')
    assert flow.pair_context(0, 1)['topic_maintenance'] > 0.2
    assert flow.pair_context(2, 3)['topic_maintenance'] == 0.0


def test_late_night_flag():
    messages = [
        {'sender': 'A', 'message': 'still awake?', 'datetime': datetime(2024, 1, 15, 23, 30)},
        {'sender': 'B', 'message': 'yeah cannot sleep', 'datetime': datetime(2024, 1, 15, 23, 40)},
    ]
    context = ConversationContext(messages, 'A', 'B').pair_context(0, 1)
    assert context['is_late_night'] == 1.0
    assert context['is_daytime'] == 0.0


def test_missing_timestamps_flagged_not_invented():
    messages = [
        {'sender': 'A', 'message': 'hey', 'datetime': None},
        {'sender': 'B', 'message': 'hello', 'datetime': None},
    ]
    context = ConversationContext(messages, 'A', 'B').pair_context(0, 1)
    assert context['timing_available'] == 0.0
    assert context['response_speed_abs'] == 0.5      # neutral, not fabricated


def test_initiation_stats_count_revivals():
    messages = [
        {'sender': 'A', 'message': 'hey', 'datetime': datetime(2024, 1, 15, 10, 0)},
        {'sender': 'B', 'message': 'hi', 'datetime': datetime(2024, 1, 15, 10, 5)},
        # 2-day silence, then A restarts
        {'sender': 'A', 'message': 'you there?', 'datetime': datetime(2024, 1, 17, 10, 0)},
        {'sender': 'B', 'message': 'yeah sorry', 'datetime': datetime(2024, 1, 17, 10, 30)},
    ]
    summary = ConversationContext(messages, 'A', 'B').timing_summary()
    assert summary['you_restarted_chat'] == 1
    assert summary['they_restarted_chat'] == 0


# --- feature extraction ----------------------------------------------------

def test_feature_width_matches_declared_dim():
    service = ConversationAnalysisService()
    features = service.extract_features('hey how was your day?', 'it was greatt!! you??')
    assert len(features) == FEATURE_DIM


def test_context_changes_features():
    """Timing context must actually reach the vector, not be silently dropped."""
    service = ConversationAnalysisService()
    fast = ConversationContext(_chat([1, 1, 1]), 'A', 'B').pair_context(0, 1)
    slow = ConversationContext(_chat([900, 900, 900]), 'A', 'B').pair_context(0, 1)

    a = service.extract_features('hey', 'hello', fast)
    b = service.extract_features('hey', 'hello', slow)
    assert not (a == b).all()


def test_features_are_finite():
    service = ConversationAnalysisService()
    import numpy as np
    for yours, theirs in [
        ('hey', 'k'),
        ('', 'something'),
        ('a' * 500, 'b' * 500),
        ('😂😂😂', '😍❤️✨'),
        ('what?', '<Media omitted>'),
    ]:
        features = service.extract_features(yours or ' ', theirs)
        assert np.all(np.isfinite(features)), (yours, theirs)


# --- end-to-end ------------------------------------------------------------

def test_analysis_includes_timing_section():
    decoded = _decode(
        "\n".join(
            f"15/01/2024, 10:{minute:02d}:00 - "
            f"{'Aarav' if minute % 2 == 0 else 'Maya'}: "
            f"{'so what do you think about the Goa trip?' if minute % 2 == 0 else 'the Goa trip sounds amazing! when are we going?'}"
            for minute in range(0, 20)
        )
    )
    result = ConversationAnalysisService().analyze_conversation(decoded['messages'])
    assert 'timing_analysis' in result
    assert result['timing_analysis']['timing_available'] is True
    assert result['timing_analysis']['their_median_reply_minutes'] is not None
    assert 0 <= result['interest_percentage'] <= 100


def test_report_renders_without_timestamps():
    decoded = _decode(
        "Aarav: hey what do you think about the trip?\n"
        "Maya: sounds good to me honestly\n"
        "Aarav: should we book it then?\n"
        "Maya: yeah lets do it\n"
    )
    service = ConversationAnalysisService()
    result = service.analyze_conversation(decoded['messages'])
    text = service.format_analysis_as_text(result)
    assert 'CONVERSATION ANALYSIS REPORT' in text
    # No timing section should be claimed when there are no timestamps.
    assert 'REPLY TIMING' not in text


# --- corpus / training parity ---------------------------------------------

def test_corpus_round_trips_through_decoder():
    """
    The training script's parity guarantee: a generated conversation rendered as
    an export and read back must reproduce the same senders and timestamps.
    """
    from training.realistic_conversation_corpus import CorpusGenerator

    generator = CorpusGenerator(seed=7)
    checked = 0
    for conversation in generator.generate(25):
        if not conversation.messages:
            continue
        decoded = _decode(conversation.to_whatsapp_export())['messages']
        assert len(decoded) == len(conversation.messages)
        for original, parsed in zip(conversation.messages, decoded):
            assert parsed['sender'] == original['sender']
            assert parsed['datetime'] == original['datetime']
        checked += 1
    assert checked >= 20


def test_corpus_labels_track_latent_interest():
    """Keen scenarios must label higher than ghosting ones, on average."""
    from training.realistic_conversation_corpus import CorpusGenerator
    import numpy as np

    keen, cold = [], []
    for scenario, sink in (('new_match_keen', keen), ('ghosting', cold)):
        generator = CorpusGenerator(seed=11, scenarios=[scenario])
        for conversation in generator.generate(40):
            sink.extend(label for _, _, label in conversation.pair_labels)

    assert keen and cold
    assert np.mean(keen) > np.mean(cold) + 1.5


def test_corpus_timestamps_are_monotonic():
    from training.realistic_conversation_corpus import CorpusGenerator

    for conversation in CorpusGenerator(seed=3).generate(30):
        stamps = [m['datetime'] for m in conversation.messages]
        assert stamps == sorted(stamps), conversation.scenario


def test_confound_scenarios_break_naive_cues():
    """
    The point of the confounds: latency alone and length alone must not separate
    interested from uninterested. If they did, the old model would have been
    fine and this dataset would be pointless.
    """
    from training.realistic_conversation_corpus import CorpusGenerator
    import numpy as np

    def reply_lengths(scenario):
        generator = CorpusGenerator(seed=5, scenarios=[scenario])
        lengths = []
        for conversation in generator.generate(40):
            for _, their_index, _ in conversation.pair_labels:
                lengths.append(len(conversation.messages[their_index]['message'].split()))
        return lengths

    # Long replies from a disinterested person, short replies from a keen one.
    polite = reply_lengths('polite_disinterest')
    dry_keen = reply_lengths('dry_texter_interested')
    assert np.mean(polite) > np.mean(dry_keen)


def _run_all():
    tests = [(name, obj) for name, obj in sorted(globals().items())
             if name.startswith('test_') and callable(obj)]
    passed, failed = 0, []
    for name, test in tests:
        try:
            test()
            passed += 1
            print(f"  PASS  {name}")
        except Exception as exc:
            failed.append((name, exc))
            print(f"  FAIL  {name}: {exc}")

    print(f"\n{passed}/{len(tests)} passed")
    if failed:
        print("\nFailures:")
        for name, exc in failed:
            print(f"  {name}: {type(exc).__name__}: {exc}")
    return 1 if failed else 0


if __name__ == '__main__':
    sys.exit(_run_all())
