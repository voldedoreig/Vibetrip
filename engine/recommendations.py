"""Spot recommendation and timing matching engine for VibeTrip.

Recommends the right places to visit and best times to go, grouped by category
(Culture, Nature, Food, Adventure, Spiritual) rather than a rigid timetable.
"""

from typing import Any, Dict, List, Optional
from engine.festivals import find_festivals_for_trip
from engine.scoring import MAX_DISTANCE, TRAITS, compute_ideal_point, distance
from engine.storage import load_activities
from engine.vibes import choose_vibe

TRAIT_WORDS: Dict[str, str] = {
    "energy": "energy & vitality",
    "crowd": "lively human buzz",
    "culture": "ancient art & traditions",
    "nature": "serene natural beauty",
    "food": "authentic culinary delights",
    "spiritual": "peaceful soul-reflection",
    "adventure": "outdoor thrill & exploration",
}

SEASON_INSIGHTS: Dict[str, Dict[str, str]] = {
    "autumn": {
        "title": "Autumn (September – November) • Peak Himalayan Season",
        "weather": "Crisp blue skies, dry comfortable trails, and crystal-clear mountain visibility.",
        "tip": "Best overall time to visit Kathmandu. The valley is buzzing with grand Dashain and Tihar festivities.",
        "best_hours_summary": "Crisp early mornings for Himalayan views; warm sunny afternoons for palace courtyards.",
    },
    "spring": {
        "title": "Spring (March – May) • Rhododendron & Blossom Season",
        "weather": "Mild, warm temperatures with blooming rhododendrons in the surrounding hills.",
        "tip": "Incredible time for photography, outdoor cultural festivals (Holi, Bisket Jatra), and pottery walks.",
        "best_hours_summary": "Comfortable from dawn until dusk; sunset terrace dinners are delightful.",
    },
    "winter": {
        "title": "Winter (December – February) • Crisp & Peaceful",
        "weather": "Cold, foggy mornings giving way to bright, warm sunshine by midday. Cold nights.",
        "tip": "Fewer tourist crowds, peaceful stupas, and extraordinary snow-capped mountain clarity by midday.",
        "best_hours_summary": "10:30 AM to 4:00 PM is prime visiting time to bask in the warm winter sun.",
    },
    "monsoon": {
        "title": "Summer / Monsoon (June – August) • Lush & Emerald Green",
        "weather": "Frequent refreshing rain showers, lush emerald valleys, and mist-shrouded hills.",
        "tip": "Best time for uncrowded temple visits, quiet rooftop cafes, budget travel, and vibrant green rice terraces.",
        "best_hours_summary": "Mornings before the afternoon showers; evenings for indoor food walks and music.",
    },
    "flexible": {
        "title": "Year-Round Travel Opportunities",
        "weather": "Kathmandu Valley offers unique beauty across all four distinct Himalayan seasons.",
        "tip": "Autumn (Oct–Nov) is best for mountain views, Spring (Mar–Apr) for flowers and festivals, and Winter for quiet charm.",
        "best_hours_summary": "Early mornings (6:30 AM – 9:00 AM) and Golden Hour (4:30 PM – 6:30 PM) offer the finest light year-round.",
    },
}


def build_spot_reason(ideal: Dict[str, float], best_visiting_hours: str) -> str:
    """Generate a friendly personalized sentence explaining why this spot was selected."""
    best_trait = max(TRAITS, key=lambda t: ideal.get(t, 0.0))
    trait_phrase = TRAIT_WORDS.get(best_trait, "unique experiences")
    return f"Perfect match for your love of {trait_phrase}. Visit during {best_visiting_hours} for the finest experience."


def get_recommendations(
    profile: Dict[str, float],
    preferred_slot: str = "morning",
    budget_level: int = 2,
    timing_info: Optional[Dict[str, Any]] = None,
    destination: str = "kathmandu",
) -> Dict[str, Any]:
    """Build destination and timing recommendations with spots grouped by category."""
    if timing_info is None:
        timing_info = {"season": "flexible", "months": [], "start_date": None}

    winning_vibe, match_pct, runners_up = choose_vibe(profile)
    ideal = compute_ideal_point(winning_vibe["target"], profile)
    all_activities = load_activities(destination=destination)

    chosen_season = timing_info.get("season", "flexible")
    chosen_months = timing_info.get("months", [])
    scored_places: List[Dict[str, Any]] = []

    for act in all_activities:
        dist = distance(act.get("traits", {}), ideal)
        raw_score = 1.0 - (dist / MAX_DISTANCE)

        if preferred_slot in act.get("slots", []):
            raw_score += 0.05

        act_months = act.get("best_months", [])
        if chosen_months and act_months and any(m in chosen_months for m in act_months):
            raw_score += 0.05

        place_match_pct = max(40, min(99, round(raw_score * 100)))
        reason = build_spot_reason(ideal, act.get("best_visiting_hours", "daylight hours"))

        scored_places.append({
            "id": act["id"],
            "name": act["name"],
            "name_ne": act.get("name_ne"),
            "description": act.get("description", ""),
            "category": act.get("category", ""),
            "category_group": act.get("category_group", "Culture"),
            "match_percent": place_match_pct,
            "cost_level": act.get("cost_level", 1),
            "duration_hours": act.get("duration_hours", 2.0),
            "location": act.get("location", "Kathmandu Valley"),
            "best_visiting_hours": act.get("best_visiting_hours", "Morning to Afternoon"),
            "best_season": act.get("best_season", "Year-Round"),
            "image": act.get("image", ""),
            "why_visit": reason,
            "slots": act.get("slots", []),
        })

    scored_places.sort(key=lambda p: -p["match_percent"])

    categories = [
        {"id": "Culture", "name": "Culture & Ancient Heritage", "icon": ""},
        {"id": "Nature", "name": "Nature & Panoramic Viewpoints", "icon": ""},
        {"id": "Food", "name": "Food & Street Flavours", "icon": ""},
        {"id": "Adventure", "name": "Adventure & Outdoor Trails", "icon": ""},
        {"id": "Spiritual", "name": "Spiritual & Peaceful Sanctuaries", "icon": ""},
    ]

    grouped_places = {
        cat["id"]: [p for p in scored_places if p.get("category_group") == cat["id"]][:4]
        for cat in categories
    }

    season_key = chosen_season if chosen_season in SEASON_INSIGHTS else "flexible"
    timing_overview = SEASON_INSIGHTS[season_key]

    start_date = timing_info.get("start_date")
    festival_highlights, also_happening = find_festivals_for_trip(
        vibe_id=winning_vibe["id"],
        days=3,
        start_date=start_date,
    )

    return {
        "vibe": winning_vibe,
        "match_percent": match_pct,
        "runners_up": runners_up,
        "profile": profile,
        "preferred_slot": preferred_slot,
        "budget_level": budget_level,
        "timing_info": timing_info,
        "timing_overview": timing_overview,
        "categories": categories,
        "grouped_places": grouped_places,
        "top_overall_highlights": scored_places[:3],
        "festival_highlights": list(festival_highlights.values()),
        "also_happening": also_happening,
    }
