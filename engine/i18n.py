"""Internationalisation (i18n) support for VibeTrip.

Loads translation dictionaries and provides dot-notation lookup for Jinja templates.
"""

from typing import Any, Dict, List, Optional
from engine.storage import load_json

_TRANSLATION_CACHE: Dict[str, Dict[str, Any]] = {}


def get_translations(lang_code: str = "en") -> Dict[str, Any]:
    """Load translation dictionary for the given language code ('en' or 'ne')."""
    clean_code = "ne" if lang_code == "ne" else "en"
    if clean_code in _TRANSLATION_CACHE:
        return _TRANSLATION_CACHE[clean_code]

    try:
        data = load_json(f"data/i18n/{clean_code}.json")
    except Exception:
        data = load_json("data/i18n/en.json")

    _TRANSLATION_CACHE[clean_code] = data
    return data


def _lookup_path(data: Dict[str, Any], parts: List[str]) -> Optional[Any]:
    curr: Any = data
    for part in parts:
        if isinstance(curr, dict) and part in curr:
            curr = curr[part]
        else:
            return None
    return curr


def translate(key: str, lang_code: str = "en", **kwargs: Any) -> str:
    """Look up a nested dot-notation key (e.g. 'nav.home' or 'planner.next')."""
    parts = key.split(".")
    val = _lookup_path(get_translations(lang_code), parts)
    if val is None and lang_code != "en":
        val = _lookup_path(get_translations("en"), parts)

    if val is None:
        return key

    result = str(val) if not isinstance(val, str) else val
    if kwargs:
        try:
            return result.format(**kwargs)
        except Exception:
            return result
    return result


def get_localized_name(item: Dict[str, Any], lang_code: str = "en") -> str:
    """Return the localized name for an item based on language preference."""
    if lang_code == "ne" and item.get("name_ne"):
        return item["name_ne"]
    return item.get("name", "")
