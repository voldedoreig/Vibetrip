"""Festival linking for VibeTrip.

Finds real Nepali festivals that overlap trip dates and match the traveler's vibe.
Supports Bikram Sambat (BS) date conversion if nepali-datetime is installed.
"""

import datetime
import logging
from typing import Any, Dict, List, Optional, Tuple
from engine.storage import load_festivals
from engine.utils import parse_date

logger = logging.getLogger(__name__)

try:
    import nepali_datetime
    HAS_NEPALI_DATETIME = True
except ImportError:
    HAS_NEPALI_DATETIME = False


def get_bs_date(gregorian_date: datetime.date) -> Optional[str]:
    """Return Bikram Sambat date string (e.g. '2082 Falgun 19 BS') if supported."""
    if not HAS_NEPALI_DATETIME:
        return None
    try:
        bs_dt = nepali_datetime.date.from_datetime_date(gregorian_date)
        return bs_dt.strftime("%Y %B %d BS")
    except Exception as e:
        logger.debug(f"Bikram Sambat conversion notice: {e}")
        return None


def find_festivals_for_trip(
    vibe_id: str,
    days: int,
    start_date: Optional[str],
) -> Tuple[Dict[int, Dict[str, Any]], List[Dict[str, Any]]]:
    """Find highlights and secondary festivals occurring during a trip."""
    start_dt = parse_date(start_date)
    if not start_dt:
        return {}, []

    trip_end_dt = start_dt + datetime.timedelta(days=days - 1)
    festival_list = load_festivals(year=start_dt.year)

    day_highlights: Dict[int, Dict[str, Any]] = {}
    also_happening: List[Dict[str, Any]] = []

    for fest in festival_list:
        fest_start = parse_date(fest.get("start"))
        fest_end = parse_date(fest.get("end"))
        if not fest_start or not fest_end:
            continue

        if max(start_dt, fest_start) > min(trip_end_dt, fest_end):
            continue

        weight = float(fest.get("vibes", {}).get(vibe_id, 0.0))

        if weight >= 0.7:
            assigned_day = None
            for d_idx in range(1, days + 1):
                cur_dt = start_dt + datetime.timedelta(days=d_idx - 1)
                if fest_start <= cur_dt <= fest_end:
                    assigned_day = d_idx
                    break

            if assigned_day is not None and assigned_day not in day_highlights:
                day_highlights[assigned_day] = {
                    "festival_id": fest["id"],
                    "name": fest["name"],
                    "name_ne": fest.get("name_ne"),
                    "slot": fest.get("slot", "afternoon"),
                    "description": fest.get("description", ""),
                    "location": fest.get("location", ""),
                    "verify_note": fest.get("verify_note", ""),
                }
            else:
                also_happening.append(fest)
        elif 0.4 <= weight < 0.7:
            also_happening.append(fest)

    return day_highlights, also_happening
