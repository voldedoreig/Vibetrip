"""Transforms user quiz answers into a structured traveler profile and trip constraints."""

from typing import Any, Dict, List, Optional, Tuple
from engine.scoring import TRAITS
from engine.storage import load_quiz
from engine.utils import parse_date


def build_profile(
    form_answers: Dict[str, str],
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
) -> Tuple[Dict[str, float], str, int, int, Optional[str]]:
    """Convert form submission answers into a traveler profile and trip constraints."""
    quiz_data = load_quiz()
    trait_buckets: Dict[str, List[float]] = {trait: [] for trait in TRAITS}

    preferred_slot = "morning"
    budget_level = 2
    days = 3

    for q in quiz_data:
        chosen_value = form_answers.get(q["id"])
        if not chosen_value:
            continue

        for opt in q.get("options", []):
            if opt["value"] == chosen_value:
                if "traits" in opt:
                    weight = 2 if q["id"] == "q4_interests" else 1
                    for trait_name, val in opt["traits"].items():
                        if trait_name in trait_buckets:
                            trait_buckets[trait_name].extend([float(val)] * weight)

                if "preferred_slot" in opt:
                    preferred_slot = str(opt["preferred_slot"]).lower()

                if "budget_level" in opt:
                    budget_level = int(opt["budget_level"])

                if "days" in opt:
                    days = int(opt["days"])

                break

    raw_start = (start_date or form_answers.get("start_date") or "").strip()
    raw_end = (end_date or form_answers.get("end_date") or "").strip()

    explicit_days = form_answers.get("trip_days") or form_answers.get("days")
    if explicit_days:
        try:
            days = max(1, min(7, int(explicit_days)))
        except (ValueError, TypeError):
            pass
    elif raw_start and raw_end:
        s_dt = parse_date(raw_start)
        e_dt = parse_date(raw_end)
        if s_dt and e_dt:
            diff = (e_dt - s_dt).days
            days = max(1, min(7, diff))

    profile: Dict[str, Any] = {}
    for trait in TRAITS:
        values = trait_buckets[trait]
        profile[trait] = round(sum(values) / len(values), 2) if values else 1.0

    profile["raw_answers"] = {k: v for k, v in form_answers.items() if v}
    clean_start_date = raw_start or None

    return profile, preferred_slot, budget_level, days, clean_start_date


def get_timing_details(form_answers: Dict[str, str], start_date: Optional[str] = None) -> Dict[str, Any]:
    """Extract timing parameters (season, months, dates) from quiz answers."""
    quiz_data = load_quiz()
    timing_choice = form_answers.get("q7_timing", "flexible")

    season = "flexible"
    months = []

    for q in quiz_data:
        if q["id"] == "q7_timing":
            for opt in q.get("options", []):
                if opt["value"] == timing_choice:
                    season = opt.get("season", "flexible")
                    months = opt.get("months", [])
                    break
            break

    raw_start = start_date.strip() if start_date and start_date.strip() else None
    if not raw_start and form_answers.get("start_date"):
        raw_start = form_answers.get("start_date", "").strip() or None

    return {
        "timing_choice": timing_choice,
        "season": season,
        "months": months,
        "start_date": raw_start,
        "end_date": form_answers.get("end_date", "").strip() or None,
    }
