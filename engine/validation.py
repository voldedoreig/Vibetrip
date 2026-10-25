"""Server-side form validation for VibeTrip inputs."""

import datetime
from typing import Any, Dict, Optional, Tuple
from engine.storage import load_quiz
from engine.utils import get_today, parse_date


def validate_planner_form(
    form_data: Dict[str, Any],
    today: Optional[datetime.date] = None,
) -> Tuple[bool, Dict[str, str]]:
    """Validate 8 quiz answers and optional start date."""
    errors: Dict[str, str] = {}
    quiz_questions = load_quiz()

    for q in quiz_questions:
        q_id = q["id"]
        val = form_data.get(q_id)
        if not val or not str(val).strip():
            errors[q_id] = f"Please select an option for '{q['text']}'"
            continue

        valid_options = {opt["value"] for opt in q.get("options", [])}
        if val not in valid_options:
            errors[q_id] = "Invalid option selected."

    start_date_val = form_data.get("start_date")
    if start_date_val and str(start_date_val).strip():
        date_str = str(start_date_val).strip()
        parsed_date = parse_date(date_str)
        if not parsed_date:
            errors["start_date"] = "Invalid date format. Please use YYYY-MM-DD."
        else:
            curr_today = today if today is not None else get_today()
            one_year_ahead = curr_today + datetime.timedelta(days=366)
            if parsed_date < curr_today:
                errors["start_date"] = "Start date must be today or a future date."
            elif parsed_date > one_year_ahead:
                errors["start_date"] = "Start date cannot be more than one year ahead."

    return len(errors) == 0, errors


def validate_feedback_form(form_data: Dict[str, Any]) -> Tuple[bool, Dict[str, str]]:
    """Validate feedback submission fields."""
    errors: Dict[str, str] = {}

    rating_raw = form_data.get("rating")
    if not rating_raw:
        errors["rating"] = "Please select a rating from 1 to 5 stars."
    else:
        try:
            rating_int = int(rating_raw)
            if not 1 <= rating_int <= 5:
                errors["rating"] = "Rating must be between 1 and 5."
        except ValueError:
            errors["rating"] = "Rating must be a number from 1 to 5."

    recommend = str(form_data.get("recommend", "")).strip().lower()
    if recommend not in ["yes", "no"]:
        errors["recommend"] = "Please indicate if you would recommend VibeTrip (Yes or No)."

    comment = str(form_data.get("comment", "")).strip()
    if len(comment) > 500:
        errors["comment"] = "Comment cannot exceed 500 characters."

    name = str(form_data.get("name", "")).strip()
    if len(name) > 80:
        errors["name"] = "Name cannot exceed 80 characters."

    return len(errors) == 0, errors


def validate_contact_form(form_data: Dict[str, Any]) -> Tuple[bool, Dict[str, str]]:
    """Validate contact submission fields."""
    errors: Dict[str, str] = {}

    name = str(form_data.get("name", "")).strip()
    if not name:
        errors["name"] = "Please enter your name."
    elif len(name) > 80:
        errors["name"] = "Name cannot exceed 80 characters."

    email = str(form_data.get("email", "")).strip()
    if not email:
        errors["email"] = "Please enter your email address."
    elif len(email) > 120:
        errors["email"] = "Email address is too long."
    elif "@" not in email:
        errors["email"] = "Email must contain an '@' symbol."
    else:
        domain_part = email.split("@", 1)[1]
        if "." not in domain_part or len(domain_part.split(".")[-1]) < 2:
            errors["email"] = "Email must contain a valid domain (e.g. name@example.com)."

    message = str(form_data.get("message", "")).strip()
    if not message:
        errors["message"] = "Please enter your message."
    elif len(message) > 1000:
        errors["message"] = "Message cannot exceed 1000 characters."

    return len(errors) == 0, errors


def validate_signup_form(form_data: Dict[str, Any]) -> Tuple[bool, Dict[str, str]]:
    """Validate user registration inputs."""
    errors: Dict[str, str] = {}
    username = str(form_data.get("username", "")).strip()
    email = str(form_data.get("email", "")).strip().lower()
    password = str(form_data.get("password", "")).strip()

    if not username:
        errors["username"] = "Please choose a username."
    elif len(username) < 3:
        errors["username"] = "Username must be at least 3 characters."
    elif len(username) > 30:
        errors["username"] = "Username cannot exceed 30 characters."

    if not email:
        errors["email"] = "Please enter your email."
    elif "@" not in email or "." not in email:
        errors["email"] = "Please provide a valid email address."

    if not password:
        errors["password"] = "Please choose a password."
    elif len(password) < 4:
        errors["password"] = "Password must be at least 4 characters."

    return len(errors) == 0, errors


def validate_login_form(form_data: Dict[str, Any]) -> Tuple[bool, Dict[str, str]]:
    """Validate user login inputs."""
    errors: Dict[str, str] = {}
    username_or_email = str(form_data.get("username_or_email", "")).strip()
    password = str(form_data.get("password", "")).strip()

    if not username_or_email:
        errors["username_or_email"] = "Please enter your username or email."
    if not password:
        errors["password"] = "Please enter your password."

    return len(errors) == 0, errors
