"""Vibe selection and matching for traveler profiles."""

from typing import Any, Dict, List, Optional, Tuple
from engine.scoring import distance, match_percent
from engine.storage import load_vibes


def choose_vibe(
    profile: Dict[str, float],
    vibes_data: Optional[List[Dict[str, Any]]] = None,
) -> Tuple[Dict[str, Any], int, List[str]]:
    """Determine the winning vibe and top 2 runners-up for a traveler profile."""
    if vibes_data is None:
        vibes_data = load_vibes()

    if not vibes_data:
        raise ValueError("No vibes found in data source.")

    scored_vibes = [
        {
            "vibe": vibe,
            "distance": distance(profile, vibe["target"]),
            "match_percent": match_percent(profile, vibe["target"]),
            "id": vibe["id"],
        }
        for vibe in vibes_data
    ]

    scored_vibes.sort(key=lambda item: (item["distance"], item["id"]))
    winner = scored_vibes[0]
    runners_up = [item["id"] for item in scored_vibes[1:3]]

    return winner["vibe"], winner["match_percent"], runners_up


def get_vibe_by_id(
    vibe_id: str,
    vibes_data: Optional[List[Dict[str, Any]]] = None,
) -> Optional[Dict[str, Any]]:
    """Retrieve a full vibe dictionary by ID."""
    if vibes_data is None:
        vibes_data = load_vibes()

    for vibe in vibes_data:
        if vibe["id"] == vibe_id:
            return vibe
    return None
