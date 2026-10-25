"""Shared utilities for date parsing, formatting, and common operations."""

import datetime
from typing import Optional


def parse_date(value: Optional[str]) -> Optional[datetime.date]:
    """Safely parse an ISO date string (YYYY-MM-DD), returning None on error."""
    if not value or not isinstance(value, str):
        return None
    clean = value.strip()
    if not clean:
        return None
    try:
        return datetime.date.fromisoformat(clean)
    except (ValueError, TypeError):
        return None


def get_today() -> datetime.date:
    """Return today's date."""
    return datetime.date.today()


def get_today_iso() -> str:
    """Return today's date as an ISO string (YYYY-MM-DD)."""
    return datetime.date.today().isoformat()


def get_now_iso() -> str:
    """Return the current timestamp as an ISO string."""
    return datetime.datetime.now().isoformat()
