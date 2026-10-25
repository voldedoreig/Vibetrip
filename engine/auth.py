"""User authentication and tour research management for VibeTrip.

Handles user signup, login, session validation, and saving tour research
(saved places, custom notes, and matched itineraries) into local JSON files.
"""

import re
from typing import Any, Dict, List, Optional, Tuple
from werkzeug.security import check_password_hash, generate_password_hash

from engine.storage import (
    get_place_by_id,
    load_plan,
    load_research,
    load_users,
    save_research,
    save_users,
)
from engine.utils import get_now_iso


def _default_user_research() -> Dict[str, Any]:
    """Default storage structure for a user's tour planning research."""
    return {
        "saved_places": [],
        "saved_plans": [],
        "notes": {},
    }


def _get_user_research_entry(research: Dict[str, Any], username: str) -> Dict[str, Any]:
    """Return or initialize the research entry for a user."""
    return research.setdefault(username, _default_user_research())


def register_user(username: str, email: str, password: str) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
    """Register a new user account."""
    clean_username = username.strip()
    clean_email = email.strip().lower()

    if len(clean_username) < 3:
        return False, "Username must be at least 3 characters long.", None

    if not re.match(r"^[a-zA-Z0-9_.-]+$", clean_username):
        return False, "Username can only contain letters, numbers, dots, and underscores.", None

    if "@" not in clean_email or "." not in clean_email:
        return False, "Please provide a valid email address.", None

    if len(password) < 4:
        return False, "Password must be at least 4 characters long.", None

    users = load_users()
    for existing_user in users.values():
        if existing_user.get("username", "").lower() == clean_username.lower():
            return False, f"Username '{clean_username}' is already taken. Please choose another.", None
        if existing_user.get("email", "").lower() == clean_email:
            return False, "An account with this email address already exists. Please sign in instead.", None

    new_user = {
        "username": clean_username,
        "email": clean_email,
        "password_hash": generate_password_hash(password),
        "created_at": get_now_iso(),
    }
    users[clean_username] = new_user
    save_users(users)

    research = load_research()
    if clean_username not in research:
        research[clean_username] = _default_user_research()
        save_research(research)

    safe_user = {
        "username": clean_username,
        "email": clean_email,
        "created_at": new_user["created_at"],
    }
    return True, "", safe_user


def authenticate_user(username_or_email: str, password: str) -> Optional[Dict[str, Any]]:
    """Verify credentials and return public profile if matching.

    Supports case-insensitive matching by username or email, handles multiple
    potential aliases, and tolerates leading/trailing accidental whitespace.
    """
    query = username_or_email.strip().lower()
    if not query or not password:
        return None

    users = load_users()
    clean_password = password.strip()

    # Collect all matching user accounts (by username or email)
    matching_users: List[Dict[str, Any]] = []
    for u in users.values():
        if u.get("username", "").lower() == query or u.get("email", "").lower() == query:
            matching_users.append(u)

    for target_user in matching_users:
        stored_hash = target_user.get("password_hash", "")
        if not stored_hash:
            continue
        if check_password_hash(stored_hash, password) or (clean_password and check_password_hash(stored_hash, clean_password)):
            return {
                "username": target_user["username"],
                "email": target_user.get("email", ""),
                "created_at": target_user.get("created_at", ""),
            }

    return None


def get_user_profile(username: str) -> Optional[Dict[str, Any]]:
    """Return user info by username without exposing password hash."""
    users = load_users()
    u = users.get(username)
    if not u:
        clean = username.strip().lower()
        for candidate in users.values():
            if candidate.get("username", "").lower() == clean or candidate.get("email", "").lower() == clean:
                u = candidate
                break
    if not u:
        return None
    return {
        "username": u.get("username", username),
        "email": u.get("email", ""),
        "created_at": u.get("created_at", ""),
    }


def get_user_research(username: str) -> Dict[str, Any]:
    """Return all saved tour planning data for a user."""
    research = load_research()
    return research.get(username, _default_user_research())


def toggle_save_place(username: str, place_id: str) -> Tuple[bool, int]:
    """Toggle a place in the user's saved wishlist."""
    research = load_research()
    user_entry = _get_user_research_entry(research, username)
    saved = user_entry.setdefault("saved_places", [])
    clean_id = place_id.strip().lower()

    if clean_id in saved:
        saved.remove(clean_id)
        is_saved = False
    else:
        saved.append(clean_id)
        is_saved = True

    save_research(research)
    return is_saved, len(saved)


def is_place_saved(username: Optional[str], place_id: str) -> bool:
    """Check if a specific place is already saved by the user."""
    if not username:
        return False
    user_data = get_user_research(username)
    clean_id = place_id.strip().lower()
    return clean_id in [p.lower() for p in user_data.get("saved_places", [])]


def get_user_saved_places(username: str) -> List[Dict[str, Any]]:
    """Return destination objects for all places saved by the user."""
    user_data = get_user_research(username)
    saved_ids = user_data.get("saved_places", [])
    notes = user_data.get("notes", {})

    places = []
    for pid in saved_ids:
        place_obj = get_place_by_id(pid)
        if place_obj:
            place_copy = dict(place_obj)
            place_copy["user_note"] = notes.get(pid, "")
            places.append(place_copy)

    return places


def update_place_note(username: str, place_id: str, note_text: str) -> bool:
    """Save or update a personal note on a destination."""
    research = load_research()
    user_entry = _get_user_research_entry(research, username)
    notes = user_entry.setdefault("notes", {})
    clean_id = place_id.strip().lower()

    if note_text.strip():
        notes[clean_id] = note_text.strip()
    else:
        notes.pop(clean_id, None)

    save_research(research)
    return True


def save_plan_for_user(username: str, plan_id: str) -> bool:
    """Add a generated tour plan ID to the user's research."""
    if not username or not plan_id:
        return False
    research = load_research()
    user_entry = _get_user_research_entry(research, username)
    plans = user_entry.setdefault("saved_plans", [])

    if plan_id not in plans:
        plans.append(plan_id)
        save_research(research)
    return True


def get_user_saved_plans(username: str) -> List[Dict[str, Any]]:
    """Return full plan objects for all itineraries saved by the user."""
    user_data = get_user_research(username)
    plan_ids = user_data.get("saved_plans", [])

    results = []
    for pid in reversed(plan_ids):
        plan_obj = load_plan(pid)
        if plan_obj:
            results.append(plan_obj)
    return results
