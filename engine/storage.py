"""Data persistence and file loading helpers for VibeTrip.

Handles JSON and CSV storage using project-root-relative paths.
"""

import csv
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
PLANS_DIR = DATA_DIR / "plans"
PLACES_JSON = DATA_DIR / "places.json"
USERS_JSON = DATA_DIR / "users.json"
RESEARCH_JSON = DATA_DIR / "user_research.json"
FEEDBACK_CSV = DATA_DIR / "feedback.csv"
CONTACT_CSV = DATA_DIR / "contact.csv"


def ensure_directories() -> None:
    """Ensure required runtime folders exist on disk."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    PLANS_DIR.mkdir(parents=True, exist_ok=True)


def load_json(relative_path: str) -> Any:
    """Load and parse a JSON file relative to the project root."""
    file_path = BASE_DIR / relative_path
    if not file_path.exists():
        logger.error(f"JSON file not found: {file_path}")
        raise FileNotFoundError(f"Missing required data file: {relative_path}")

    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)


def _load_json_file(path: Path, default: Any = None) -> Any:
    """Read a JSON file from disk safely, returning default on missing or malformed content."""
    ensure_directories()
    if not path.exists():
        return {} if default is None else default
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error reading {path.name}: {e}")
        return {} if default is None else default


def _save_json_file(path: Path, data: Any) -> None:
    """Write data to a JSON file formatted with indentation."""
    ensure_directories()
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def load_places() -> List[Dict[str, Any]]:
    """Return all featured destination places from data/places.json."""
    return _load_json_file(PLACES_JSON, [])


def get_place_by_id(place_id: str) -> Optional[Dict[str, Any]]:
    """Find a specific featured place or Nepal activity by unique ID."""
    clean_id = place_id.strip().lower()

    for p in load_places():
        if p.get("id", "").lower() == clean_id:
            return p

    try:
        activities = load_activities("nepal")
        for act in activities:
            if act["id"].lower() == clean_id:
                cost_map = {1: "Budget Friendly", 2: "Moderate"}
                cost_str = cost_map.get(act.get("cost_level"), "Premium")
                duration = act.get("duration_hours", 2.0)
                location_str = act.get("location", "Nepal")

                return {
                    "id": act["id"],
                    "name": act["name"],
                    "name_ne": act.get("name_ne", act["name"]),
                    "country": location_str,
                    "vibe_tag": act.get("category", "Nepal Highlight"),
                    "vibe_id": act.get("category_group", "Culture").lower(),
                    "vibe_color": "#10B981",
                    "vibe_icon": "",
                    "image": act.get("image", "/static/img/places/boudhanath.jpg"),
                    "caption": act.get("description", ""),
                    "tagline": act.get("description", ""),
                    "overview": act.get("description", ""),
                    "best_hours": act.get("best_visiting_hours", "Daytime hours"),
                    "best_season": act.get("best_season", "Year-round (Autumn & Spring recommended)"),
                    "budget": f"Cost Level: {cost_str} • ~{duration} hrs",
                    "duration": f"~{duration} Hours",
                    "highlights": [
                        f"Category: {act.get('category', 'Experience')}",
                        f"Recommended Timing: {act.get('best_visiting_hours', 'Flexible')}",
                        f"Location: {location_str}",
                        f"Estimated Duration: ~{duration} hours",
                    ],
                    "travel_tips": f"Best experienced during {act.get('best_visiting_hours', 'daylight hours')}. Located in {location_str}.",
                    "fun_fact": f"A celebrated sanctuary of Nepal's natural and cultural heritage in {location_str}.",
                    "location_notes": f"Located at {location_str}.",
                }
    except Exception as e:
        logger.error(f"Error resolving activity '{clean_id}': {e}")

    return None


def load_users() -> Dict[str, Any]:
    """Load registered users dictionary from data/users.json."""
    return _load_json_file(USERS_JSON, {})


def save_users(users: Dict[str, Any]) -> None:
    """Save users dictionary to data/users.json."""
    _save_json_file(USERS_JSON, users)


def load_research() -> Dict[str, Any]:
    """Load tour planning research dictionary from data/user_research.json."""
    return _load_json_file(RESEARCH_JSON, {})


def save_research(research: Dict[str, Any]) -> None:
    """Save tour planning research to data/user_research.json."""
    _save_json_file(RESEARCH_JSON, research)


def load_vibes() -> List[Dict[str, Any]]:
    """Return all vibes defined in data/vibes.json."""
    return load_json("data/vibes.json")


def load_quiz() -> List[Dict[str, Any]]:
    """Return quiz questions defined in data/quiz.json or data/quiz_questions.json."""
    if (DATA_DIR / "quiz_questions.json").exists():
        return load_json("data/quiz_questions.json")
    return load_json("data/quiz.json")


def load_activities(destination: str = "kathmandu") -> List[Dict[str, Any]]:
    """Return activities list for the given destination folder."""
    return load_json(f"data/destinations/{destination}/activities.json")


def load_destination_meta(destination: str = "kathmandu") -> Dict[str, Any]:
    """Return metadata (currency, timezone, name) for a destination pack."""
    return load_json(f"data/destinations/{destination}/destination.json")


def load_festivals(year: int = 2026) -> List[Dict[str, Any]]:
    """Load festivals list for the given year, falling back to nearest available year."""
    festivals_dir = DATA_DIR / "festivals"
    target_file = festivals_dir / f"{year}.json"

    if target_file.exists():
        with open(target_file, "r", encoding="utf-8") as f:
            return json.load(f)

    year_files = sorted(festivals_dir.glob("*.json"))
    if year_files:
        logger.warning(f"Festival file for {year} not found; falling back to {year_files[0].name}")
        with open(year_files[0], "r", encoding="utf-8") as f:
            return json.load(f)

    logger.warning("No festival files found in data/festivals/.")
    return []


def save_plan(plan_data: Dict[str, Any]) -> str:
    """Save an itinerary plan dictionary to data/plans/<plan_id>.json."""
    ensure_directories()
    plan_id = plan_data["id"]
    file_path = PLANS_DIR / f"{plan_id}.json"

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(plan_data, f, indent=2, ensure_ascii=False)

    return plan_id


def load_plan(plan_id: str) -> Optional[Dict[str, Any]]:
    """Load a saved itinerary by unique plan ID."""
    clean_id = Path(plan_id).name
    file_path = PLANS_DIR / f"{clean_id}.json"

    if not file_path.exists():
        return None

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error reading plan {clean_id}: {e}")
        return None


def _append_csv(file_path: Path, fieldnames: List[str], row_data: Dict[str, Any]) -> None:
    """Helper to safely append a row to a CSV file, writing headers if missing."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    file_exists = file_path.exists()

    with open(file_path, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()
        writer.writerow({k: row_data.get(k, "") for k in fieldnames})


def append_feedback(row_data: Dict[str, Any]) -> None:
    """Append a feedback submission to data/feedback.csv."""
    fields = ["timestamp", "plan_id", "rating", "recommend", "name", "comment"]
    _append_csv(FEEDBACK_CSV, fields, row_data)


def append_contact(row_data: Dict[str, Any]) -> None:
    """Append a contact form submission to data/contact.csv."""
    fields = ["timestamp", "name", "email", "message"]
    _append_csv(CONTACT_CSV, fields, row_data)
