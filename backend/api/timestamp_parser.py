"""
Timestamp parsing for decoded conversations.

Chat exports carry the single most predictive real-life engagement signal there
is - *when* somebody replied - and every export writes it differently. This
module turns the raw timestamp strings the decoder scrapes off each line into
real ``datetime`` objects so the model can use reply latency, time-of-day and
conversation gaps instead of placeholder constants.

Handled shapes (the ones actually produced by real exports):

    WhatsApp    15/01/2024, 10:30:00      1/15/24, 10:30 PM      15.01.2024, 22:05
    Telegram    10:30:00                 22:05                  (time only)
    Instagram   10:30
    ISO / JSON  2024-01-15T14:30:00Z     2024-01-15 14:30:00    2024-01-15
    Epoch       1705329000               1705329000000 (ms)

Day/month order is genuinely ambiguous (``03/04/2024``), so it is inferred once
per file from every timestamp in it rather than guessed per line.
"""

from __future__ import annotations

import re
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

__all__ = ['infer_date_order', 'parse_timestamp', 'attach_datetimes']


# --- component patterns -----------------------------------------------------

# 15/01/2024 or 1.15.24 or 2024-01-15  (+ optional time)
_DATE_SEP = r'[/.\-]'
_NUMERIC_DATE = re.compile(
    rf'^\s*(\d{{1,4}}){_DATE_SEP}(\d{{1,2}}){_DATE_SEP}(\d{{2,4}})'
)
_TIME = re.compile(
    r'(\d{1,2}):(\d{2})(?::(\d{2}))?\s*([APap]\.?[Mm]\.?)?'
)
_EPOCH = re.compile(r'^\s*(\d{9,14})(?:\.\d+)?\s*$')

# Unicode junk WhatsApp likes to inject around am/pm markers.
_JUNK = str.maketrans({' ': ' ', ' ': ' ', '‎': '', '‏': ''})


def _clean(raw: str) -> str:
    return raw.translate(_JUNK).strip().strip('[]').strip().rstrip(',').strip()


def _split_time(text: str):
    """Return (hour, minute, second) from the first time in `text`, or None."""
    m = _TIME.search(text)
    if not m:
        return None
    hour, minute = int(m.group(1)), int(m.group(2))
    second = int(m.group(3)) if m.group(3) else 0
    meridiem = (m.group(4) or '').replace('.', '').lower()
    if meridiem == 'pm' and hour < 12:
        hour += 12
    elif meridiem == 'am' and hour == 12:
        hour = 0
    if not (0 <= hour <= 23 and 0 <= minute <= 59 and 0 <= second <= 59):
        return None
    return hour, minute, second


def _norm_year(year: int) -> int:
    """Two-digit years: 70-99 -> 1970s-1990s, 00-69 -> 2000s-2060s."""
    if year >= 100:
        return year
    return 1900 + year if year >= 70 else 2000 + year


def infer_date_order(raw_timestamps: List[Optional[str]]) -> str:
    """
    Decide whether numeric dates in this file are day-first or month-first.

    Looks for a value that can only be a day (>12) in one of the first two
    slots. WhatsApp's own default is day-first outside the US, so that is the
    tie-break when nothing in the file disambiguates.
    """
    day_first_votes = 0
    month_first_votes = 0

    for raw in raw_timestamps:
        if not raw:
            continue
        m = _NUMERIC_DATE.match(_clean(str(raw)))
        if not m:
            continue
        first, second = int(m.group(1)), int(m.group(2))
        if first > 999:          # 2024-01-15, already unambiguous
            continue
        if first > 12 and second <= 12:
            day_first_votes += 1
        elif second > 12 and first <= 12:
            month_first_votes += 1

    if month_first_votes > day_first_votes:
        return 'month_first'
    return 'day_first'


def parse_timestamp(raw: Any,
                    date_order: str = 'day_first',
                    previous: Optional[datetime] = None) -> Optional[datetime]:
    """
    Parse one raw timestamp into a datetime.

    Args:
        raw: the timestamp as scraped (string, int epoch, or None).
        date_order: 'day_first' or 'month_first', from `infer_date_order`.
        previous: the previous message's datetime. Used for time-only formats
            (Telegram ``[22:05]``) to anchor the date and to roll over midnight
            when the clock goes backwards.

    Returns:
        A datetime, or None if `raw` carries no usable time information.
    """
    if raw is None:
        return None

    if isinstance(raw, datetime):
        return raw

    if isinstance(raw, (int, float)):
        return _from_epoch(float(raw))

    text = _clean(str(raw))
    if not text:
        return None

    epoch = _EPOCH.match(text)
    if epoch:
        return _from_epoch(float(epoch.group(1)))

    date_match = _NUMERIC_DATE.match(text)
    time_part = _split_time(text[date_match.end():] if date_match else text)

    if date_match:
        a, b, c = int(date_match.group(1)), int(date_match.group(2)), int(date_match.group(3))
        if a > 999:                                  # 2024-01-15
            year, month, day = a, b, c
        elif date_order == 'month_first':
            month, day, year = a, b, _norm_year(c)
        else:
            day, month, year = a, b, _norm_year(c)

        # A file tagged day_first can still contain an out-of-range day; swap
        # rather than drop the timestamp entirely.
        if month > 12 and day <= 12:
            day, month = month, day

        hour, minute, second = time_part or (0, 0, 0)
        try:
            return datetime(year, month, day, hour, minute, second)
        except ValueError:
            return None

    if time_part is None:
        return None

    # Time only: hang it off the previous message's date, rolling to the next
    # day when the clock appears to go backwards (a chat crossing midnight).
    hour, minute, second = time_part
    anchor = previous or datetime(1970, 1, 1)
    stamp = anchor.replace(hour=hour, minute=minute, second=second, microsecond=0)
    if previous is not None and stamp < previous:
        stamp += timedelta(days=1)
    return stamp


def _from_epoch(value: float) -> Optional[datetime]:
    if value > 1e11:        # milliseconds
        value /= 1000.0
    try:
        return datetime.fromtimestamp(value)
    except (OverflowError, OSError, ValueError):
        return None


def attach_datetimes(messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Add a parsed ``datetime`` to every message, in place.

    Each message gains:
        'datetime'         -> datetime or None
        'datetime_iso'     -> ISO string or None (JSON-safe for API responses)

    Monotonicity is enforced against the previous *successfully parsed* stamp so
    one malformed line cannot drag the whole timeline backwards.
    """
    date_order = infer_date_order([m.get('timestamp') for m in messages])

    previous: Optional[datetime] = None
    for msg in messages:
        stamp = parse_timestamp(msg.get('timestamp'), date_order, previous)
        # Reject stamps that jump backwards by more than a day: exports are
        # chronological, so that means we mis-read the line, not time travel.
        if stamp and previous and stamp < previous - timedelta(days=1):
            stamp = None
        msg['datetime'] = stamp
        msg['datetime_iso'] = stamp.isoformat() if stamp else None
        if stamp:
            previous = stamp

    return messages
