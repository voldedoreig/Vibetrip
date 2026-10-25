"""Mathematical scoring, distance calculations, and coordinate geometry for VibeTrip.

Uses Euclidean distance over 7 traveler personality traits:
energy, crowd, culture, nature, food, spiritual, adventure.
"""

import math
from typing import Dict, List

TRAITS: List[str] = [
    "energy",
    "crowd",
    "culture",
    "nature",
    "food",
    "spiritual",
    "adventure",
]

# Maximum possible distance across 7 dimensions (each trait in [0, 5])
# sqrt(7 * 5^2) = sqrt(175) ≈ 13.2287
MAX_DISTANCE: float = math.sqrt(len(TRAITS) * (5.0 ** 2))


def distance(a: Dict[str, float], b: Dict[str, float]) -> float:
    """Calculate the Euclidean distance between two 7-trait points."""
    sum_squares = sum(
        (float(a.get(trait, 2.5)) - float(b.get(trait, 2.5))) ** 2
        for trait in TRAITS
    )
    return math.sqrt(sum_squares)


def match_percent(a: Dict[str, float], b: Dict[str, float]) -> int:
    """Convert trait distance into a 0-100 percentage match."""
    dist = distance(a, b)
    score = 100.0 * (1.0 - (dist / MAX_DISTANCE))
    return max(0, min(100, round(score)))


def compute_ideal_point(vibe_target: Dict[str, float], profile: Dict[str, float]) -> Dict[str, float]:
    """Calculate the blended ideal personality vector: 0.25 * vibe_target + 0.75 * profile."""
    return {
        trait: round(
            0.25 * float(vibe_target.get(trait, 2.5)) + 0.75 * float(profile.get(trait, 2.5)),
            4
        )
        for trait in TRAITS
    }


def haversine_distance_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Calculate great-circle distance between two geographic coordinates in kilometers."""
    try:
        r = 6371.0
        dlat = math.radians(lat2 - lat1)
        dlng = math.radians(lng2 - lng1)
        a = (
            math.sin(dlat / 2) ** 2
            + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlng / 2) ** 2
        )
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        return r * c
    except Exception:
        return 0.0
