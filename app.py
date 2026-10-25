"""VibeTrip - Main Flask Web Application.

Routes and page rendering only. All business logic is delegated to the engine/ package.
"""

import datetime
import os
from typing import Any, Dict

from flask import (
    Flask,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    session,
    url_for,
)

from engine.ai_generator import (
    build_dna_pills,
    calculate_transit_between_stops,
    get_action_guidance_for_activity,
    load_dotenv,
    personalize_itinerary_with_gemini,
)
from engine.auth import (
    authenticate_user,
    get_user_profile,
    get_user_research,
    get_user_saved_places,
    get_user_saved_plans,
    is_place_saved,
    register_user,
    save_plan_for_user,
    toggle_save_place,
    update_place_note,
)
from engine.festivals import HAS_NEPALI_DATETIME
from engine.i18n import get_localized_name, translate
from engine.itinerary import generate_plan
from engine.quiz import build_profile, get_timing_details
from engine.storage import (
    append_contact,
    append_feedback,
    get_place_by_id,
    load_activities,
    load_destination_meta,
    load_places,
    load_plan,
    load_quiz,
    load_vibes,
    save_plan,
)
from engine.utils import get_now_iso, get_today, get_today_iso
from engine.validation import (
    validate_contact_form,
    validate_feedback_form,
    validate_login_form,
    validate_planner_form,
    validate_signup_form,
)
from engine.vibes import choose_vibe, get_vibe_by_id

load_dotenv()

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "vibetrip-grade9-secret-key-2026")
app.config["PERMANENT_SESSION_LIFETIME"] = datetime.timedelta(days=30)
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024


@app.context_processor
def inject_template_globals() -> Dict[str, Any]:
    url_lang = request.args.get("lang")
    if url_lang in ["en", "ne"]:
        session["lang"] = url_lang
    lang = session.get("lang", "en")
    current_username = session.get("username")
    saved_count = 0
    if current_username:
        research = get_user_research(current_username)
        saved_count = len(research.get("saved_places", []))

    return {
        "current_lang": lang,
        "current_user": current_username,
        "saved_count": saved_count,
        "t": lambda key, **kwargs: translate(key, lang_code=lang, **kwargs),
        "loc": lambda item: get_localized_name(item, lang_code=lang),
        "loc_field": lambda item, field: (
            item.get(f"{field}_ne")
            if lang == "ne" and item.get(f"{field}_ne")
            else item.get(field, "")
        ),
        "all_vibes": load_vibes(),
        "get_vibe": get_vibe_by_id,
        "has_nepali_datetime": HAS_NEPALI_DATETIME,
        "now_year": get_today().year,
    }


def _is_ajax_request() -> bool:
    """Detect if the current request is an AJAX or JSON request."""
    return request.headers.get("X-Requested-With") == "XMLHttpRequest" or request.is_json


def _enrich_slot_data(slot_data: Dict[str, Any]) -> None:
    """Enrich slot data with hand-curated guidance fallbacks for legacy saved plans."""
    act_id = slot_data.get("activity_id") or slot_data.get("festival_id", "")
    guide = get_action_guidance_for_activity(act_id)

    fallback_checks = [
        ("what_to_do", "Arrive early to soak in the atmosphere. Step through the courtyard slowly"),
        ("taste_pairing", "Find an open-air rooftop"),
        ("insider_secret", "Notice the subtle architectural"),
        ("etiquette_tip", "Always walk clockwise around sacred monuments and ask"),
    ]
    for field, placeholder in fallback_checks:
        if not slot_data.get(field) or placeholder in str(slot_data.get(field, "")):
            slot_data[field] = guide.get(field)

    slot_data.setdefault(
        "transit_tip",
        guide.get("transit_tip", "Walk through pedestrian bahals or take an electric taxi outside peak rush hour."),
    )
    slot_data.setdefault("ideal_window", guide.get("ideal_window", "Morning / Dusk"))
    if not slot_data.get("lat") or not slot_data.get("lng"):
        slot_data["lat"] = guide.get("lat", 27.7172)
        slot_data["lng"] = guide.get("lng", 85.3240)
    if slot_data.get("activity_id") == "central_zoo_jawalakhel":
        slot_data["image"] = "/static/img/activities/central_zoo_jawalakhel.jpg"


INTRO_PLACES = [
    {
        "id": "boudhanath",
        "name": "Boudhanath Stupa",
        "country": "Kathmandu, Nepal",
        "vibe_tag": "Spiritual Seeker",
        "vibe_color": "#6366F1",
        "vibe_icon": "",
        "image": "/static/img/places/boudhanath.jpg",
        "caption": "Spinning brass prayer wheels in morning incense under watchful Buddha eyes.",
        "best_time": "Best at sunrise (6:00–8:30 AM)",
        "side": "left",
        "progress_threshold": 0.00,
    },
    {
        "id": "phewa_lake",
        "name": "Phewa Lake",
        "country": "Pokhara, Nepal",
        "vibe_tag": "Calm Explorer",
        "vibe_color": "#0D9488",
        "vibe_icon": "",
        "image": "/static/img/places/phewa_lake.jpg",
        "caption": "Drifting in a painted wooden doonga with snowy Annapurna peaks reflected on glass water.",
        "best_time": "Best on calm mornings (glass reflection)",
        "side": "right",
        "progress_threshold": 0.08,
    },
    {
        "id": "holi_basantapur",
        "name": "Basantapur Durbar Square",
        "country": "Kathmandu, Nepal",
        "vibe_tag": "Festival Spark",
        "vibe_color": "#E11D48",
        "vibe_icon": "",
        "image": "/static/img/places/holi_basantapur.jpg",
        "caption": "Centuries-old pagoda temples buzzing with life, pigeons, and the joyful colors of spring.",
        "best_time": "Best in March (Holi) or golden hour",
        "side": "left",
        "progress_threshold": 0.17,
    },
    {
        "id": "ebc_trail",
        "name": "Everest Base Camp Trail",
        "country": "Khumbu, Nepal",
        "vibe_tag": "Adventure Seeker",
        "vibe_color": "#D97706",
        "vibe_icon": "",
        "image": "/static/img/places/ebc_trail.jpg",
        "caption": "Suspension bridges dancing with prayer flags over turquoise glacial rivers in the high Himalayas.",
        "best_time": "Best in October & April for clear skies",
        "side": "right",
        "progress_threshold": 0.26,
    },
    {
        "id": "patan_durbar",
        "name": "Patan Durbar Square",
        "country": "Lalitpur, Nepal",
        "vibe_tag": "Heritage Historian",
        "vibe_color": "#B45309",
        "vibe_icon": "",
        "image": "/static/img/places/patan_durbar.jpg",
        "caption": "Masterpiece red-brick courtyards, stone Krishna temple carvings, and golden royal baths.",
        "best_time": "Best in late afternoon (golden light)",
        "side": "left",
        "progress_threshold": 0.35,
    },
    {
        "id": "bhaktapur_durbar",
        "name": "Bhaktapur Durbar Square",
        "country": "Bhaktapur, Nepal",
        "vibe_tag": "Heritage Historian",
        "vibe_color": "#92400E",
        "vibe_icon": "",
        "image": "/static/img/places/bhaktapur_durbar.jpg",
        "caption": "Living medieval city with soaring 5-tier Nyatapola pagoda and clay pottery squares.",
        "best_time": "Best in morning (9:00 AM–12:00 PM)",
        "side": "right",
        "progress_threshold": 0.44,
    },
    {
        "id": "swayambhunath",
        "name": "Swayambhunath Monkey Temple",
        "country": "Kathmandu, Nepal",
        "vibe_tag": "Spiritual Seeker",
        "vibe_color": "#4F46E5",
        "vibe_icon": "",
        "image": "/static/img/places/swayambhunath.jpg",
        "caption": "Ancient hilltop stupa with 365 stone stairs, sacred monkeys, and panoramic valley views.",
        "best_time": "Best at sunrise or dusk for city panorama",
        "side": "left",
        "progress_threshold": 0.53,
    },
    {
        "id": "nagarkot_sunrise",
        "name": "Nagarkot Ridge",
        "country": "Nagarkot, Nepal",
        "vibe_tag": "Calm Explorer",
        "vibe_color": "#0284C7",
        "vibe_icon": "",
        "image": "/static/img/places/nagarkot_sunrise.jpg",
        "caption": "First golden rays illuminating 8 Himalayan ranges including Langtang, Ganesh and Everest.",
        "best_time": "Best at dawn (5:30–7:00 AM)",
        "side": "right",
        "progress_threshold": 0.62,
    },
    {
        "id": "pashupatinath",
        "name": "Pashupatinath Temple",
        "country": "Kathmandu, Nepal",
        "vibe_tag": "Spiritual Seeker",
        "vibe_color": "#B91C1C",
        "vibe_icon": "",
        "image": "/static/img/places/pashupatinath.jpg",
        "caption": "Sacred Bagmati river banks illuminated by evening oil lamp Aarti and holy bells.",
        "best_time": "Best at 6:00 PM (Sandhya Aarti)",
        "side": "left",
        "progress_threshold": 0.71,
    },
    {
        "id": "rara_lake",
        "name": "Rara Lake",
        "country": "Mugu, Nepal",
        "vibe_tag": "Adventure Seeker",
        "vibe_color": "#059669",
        "vibe_icon": "",
        "image": "/static/img/places/rara_lake.jpg",
        "caption": "Queen of Himalayan lakes with crystal cobalt waters surrounded by blue pine and juniper forests.",
        "best_time": "Best in Autumn & Spring (mirror reflection)",
        "side": "right",
        "progress_threshold": 0.80,
    },
]


@app.route("/")
def home():
    """Home page: Animated scrolling travel-thread intro and main content."""
    vibes = load_vibes()
    return render_template("index.html", vibes=vibes, intro_places=INTRO_PLACES)


@app.route("/about")
def about():
    """About page: Explains the concept, 4-step process, and all 8 vibes."""
    vibes = load_vibes()
    return render_template("about.html", vibes=vibes)


@app.route("/gallery")
def gallery():
    """Gallery page: View curated sanctuaries across all of Nepal with live search and bookmarking."""
    vibes = load_vibes()
    activities = load_activities("nepal")
    username = session.get("username")
    saved_ids = []
    if username:
        user_data = get_user_research(username)
        saved_ids = [p.lower() for p in user_data.get("saved_places", [])]

    categories = [
        {"id": "all", "name": "All Categories", "icon": ""},
        {"id": "culture", "name": "Culture & Heritage", "icon": ""},
        {"id": "spiritual", "name": "Spiritual", "icon": ""},
        {"id": "nature", "name": "Nature & Views", "icon": ""},
        {"id": "food", "name": "Food & Markets", "icon": ""},
        {"id": "adventure", "name": "Adventure", "icon": ""},
    ]

    for act in activities:
        best_vibe, _, _ = choose_vibe(act.get("traits", {}), vibes)
        act["primary_vibe_id"] = best_vibe["id"]
        act["primary_vibe_name"] = best_vibe["name"]
        act["primary_vibe_icon"] = best_vibe["icon"]
        act["primary_vibe_color"] = best_vibe["theme"]["primary"]
        act["is_saved"] = act["id"].lower() in saved_ids
        act["cat_id"] = act.get("category_group", "Culture").lower()

    return render_template(
        "gallery.html",
        vibes=vibes,
        activities=activities,
        categories=categories,
        saved_ids=saved_ids,
    )


@app.route("/planner", methods=["GET", "POST"])
def planner():
    """Quiz planner: 8 questions to generate a custom itinerary."""
    quiz_questions = load_quiz()

    if request.method == "POST":
        form_data = request.form.to_dict()

        is_valid, errors = validate_planner_form(form_data)
        if not is_valid:
            return (
                render_template(
                    "planner.html",
                    quiz_questions=quiz_questions,
                    answers=form_data,
                    errors=errors,
                ),
                400,
            )

        try:
            profile, pref_slot, budget, days, start_date = build_profile(
                form_answers=form_data,
                start_date=form_data.get("start_date"),
                end_date=form_data.get("end_date"),
            )
            timing_info = get_timing_details(form_data, form_data.get("start_date"))

            dest_scope = form_data.get("destination_scope", "nepal").strip().lower()
            if dest_scope not in ["nepal", "kathmandu"]:
                dest_scope = "nepal"

            plan = generate_plan(
                profile=profile,
                preferred_slot=pref_slot,
                budget_level=budget,
                days=days,
                start_date=start_date,
                destination=dest_scope,
                timing_info=timing_info,
            )

            current_user = session.get("username")
            if current_user:
                save_plan_for_user(current_user, plan["id"])

            return redirect(url_for("results", plan_id=plan["id"]))

        except Exception as e:
            app.logger.error(f"Error generating plan: {e}")
            flash("Something went wrong, please try again.", "error")
            return (
                render_template(
                    "planner.html",
                    quiz_questions=quiz_questions,
                    answers=form_data,
                    errors={"general": "Something went wrong, please try again."},
                ),
                500,
            )

    today_iso = get_today_iso()
    return render_template("planner.html", quiz_questions=quiz_questions, answers={}, errors={}, today_iso=today_iso)


@app.template_filter("devanagari_num")
def devanagari_num_filter(value):
    num_str = f"{value:02d}" if isinstance(value, int) else str(value)
    digits = {"0": "०", "1": "१", "2": "२", "3": "३", "4": "४", "5": "५", "6": "६", "7": "७", "8": "८", "9": "९"}
    return "".join(digits.get(ch, ch) for ch in num_str)


@app.route("/results/<plan_id>")
def results(plan_id: str):
    """Results page: Day-by-day itinerary with vibe theme colors and festival highlights."""
    plan = load_plan(plan_id)
    if not plan:
        return render_template("404.html", message="Itinerary plan not found."), 404

    current_user = session.get("username")
    if current_user:
        save_plan_for_user(current_user, plan_id)

    vibe_obj = get_vibe_by_id(plan["vibe"])
    runner_up_vibes = [get_vibe_by_id(v_id) for v_id in plan.get("runners_up", [])]
    dest_meta = load_destination_meta(plan.get("destination", "kathmandu"))

    vibe_images = {
        "calm_explorer": "/static/img/places/nagarkot_sunrise.jpg",
        "festival_spark": "/static/img/places/holi_basantapur.jpg",
        "adventure_seeker": "/static/img/places/ebc_trail.jpg",
        "culture_hound": "/static/img/places/bhaktapur_durbar.jpg",
        "spiritual_seeker": "/static/img/places/boudhanath.jpg",
        "foodie_wanderer": "/static/img/places/patan_durbar.jpg",
        "family_fun": "/static/img/places/swayambhunath.jpg",
        "nature_lover": "/static/img/places/phewa_lake.jpg",
    }
    vibe_hero_image = vibe_images.get(plan.get("vibe"), "/static/img/places/boudhanath.jpg")

    has_stop_why = any(
        isinstance(s, dict) and s.get("why_for_you")
        for d in plan.get("days", [])
        for s in d.get("slots", {}).values()
    )
    if not has_stop_why or "ai_narrative" not in plan:
        plan = personalize_itinerary_with_gemini(plan)

    plan["dna_pills"] = build_dna_pills(plan, vibe_obj)

    for day in plan.get("days", []):
        day_stops = []
        for slot_name in ["morning", "afternoon", "evening"]:
            slot_data = day.get("slots", {}).get(slot_name)
            if slot_data and isinstance(slot_data, dict) and slot_data.get("name"):
                _enrich_slot_data(slot_data)
                day_stops.append(slot_data)

        for i in range(len(day_stops) - 1):
            curr_stop = day_stops[i]
            next_stop = day_stops[i + 1]
            curr_stop["next_transit_label"] = calculate_transit_between_stops(
                float(curr_stop.get("lat", 27.7172)),
                float(curr_stop.get("lng", 85.3240)),
                float(next_stop.get("lat", 27.7172)),
                float(next_stop.get("lng", 85.3240)),
            )

    save_plan(plan)

    return render_template(
        "results.html",
        plan=plan,
        vibe=vibe_obj,
        runners_up=runner_up_vibes,
        destination=dest_meta,
        vibe_hero_image=vibe_hero_image,
    )


@app.route("/api/gemini/enhance_plan", methods=["POST"])
@app.route("/api/enhance-plan", methods=["POST"])
def api_gemini_enhance():
    """Enhance an existing plan with bespoke Gemini AI narrative and stop guidance."""
    data = request.get_json(silent=True) or {}
    plan_id = data.get("plan_id")
    api_key = data.get("api_key", "").strip() or None

    plan = load_plan(plan_id)
    if not plan:
        return jsonify({"success": False, "error": "Plan not found"}), 404

    plan = personalize_itinerary_with_gemini(plan, api_key=api_key)
    save_plan(plan)
    return jsonify({
        "success": True,
        "narrative": plan.get("personalized_narrative", {}),
        "ai_narrative": plan.get("ai_narrative", {}),
        "plan": plan,
    })


@app.route("/settings")
def settings():
    """Preferences and Atmosphere Settings page."""
    return render_template("settings.html")


@app.route("/place/<place_id>")
def place_detail(place_id: str):
    """Detailed destination page: Visiting hours, seasons, budget, highlights, tips, and tour saving."""
    place = get_place_by_id(place_id)
    if not place:
        return render_template("404.html", message=f"Destination '{place_id}' was not found."), 404

    username = session.get("username")
    saved = is_place_saved(username, place_id)
    user_note = ""
    if username:
        research = get_user_research(username)
        user_note = research.get("notes", {}).get(place_id, "")

    all_places = load_places()
    related = [p for p in all_places if p["id"] != place["id"] and p.get("vibe_id") == place.get("vibe_id")]
    if not related:
        related = [p for p in all_places if p["id"] != place["id"]][:3]

    return render_template(
        "place_detail.html",
        place=place,
        is_saved=saved,
        user_note=user_note,
        related_places=related[:3],
    )


@app.route("/place/<place_id>/save", methods=["POST"])
def place_save(place_id: str):
    """Toggle saving a destination into the user's tour research wishlist."""
    username = session.get("username")
    place = get_place_by_id(place_id)
    if not place:
        return jsonify({"success": False, "error": "Destination not found"}), 404

    is_ajax = _is_ajax_request()

    if not username:
        if is_ajax:
            return jsonify({"success": False, "login_required": True, "redirect": url_for("login")}), 401
        flash("Please log in to save places to your tour research wishlist.", "info")
        return redirect(url_for("login", next=url_for("place_detail", place_id=place_id)))

    is_saved, count = toggle_save_place(username, place_id)

    if is_ajax:
        return jsonify({"success": True, "is_saved": is_saved, "count": count})

    action_msg = "saved to" if is_saved else "removed from"
    flash(f"'{place['name']}' has been {action_msg} your tour research wishlist.", "success")
    return redirect(request.referrer or url_for("place_detail", place_id=place_id))


@app.route("/place/<place_id>/note", methods=["POST"])
def place_note(place_id: str):
    """Save or update personal tour planning notes for a destination."""
    username = session.get("username")
    is_ajax = _is_ajax_request()

    if not username:
        if is_ajax:
            return jsonify({"success": False, "login_required": True}), 401
        flash("Please log in to save personal notes.", "info")
        return redirect(url_for("login"))

    note_text = request.form.get("note", "").strip()
    update_place_note(username, place_id, note_text)

    if is_ajax:
        return jsonify({"success": True, "note": note_text, "message": "Note saved!"})

    flash("Tour note updated successfully!", "success")
    return redirect(request.referrer or url_for("place_detail", place_id=place_id))


@app.route("/login", methods=["GET", "POST"])
def login():
    """User login: Access saved tour research and personal itineraries."""
    if session.get("username"):
        return redirect(url_for("my_tour"))

    next_url = request.args.get("next") or request.form.get("next")

    if request.method == "POST":
        form_data = request.form.to_dict()
        is_valid, errors = validate_login_form(form_data)

        if not is_valid:
            return render_template("login.html", answers=form_data, errors=errors, next_url=next_url), 400

        user = authenticate_user(
            username_or_email=form_data.get("username_or_email", ""),
            password=form_data.get("password", ""),
        )

        if not user:
            return (
                render_template(
                    "login.html",
                    answers=form_data,
                    errors={"auth": "Invalid username/email or password. Please try again."},
                    next_url=next_url,
                ),
                401,
            )

        session.permanent = True
        session["username"] = user["username"]
        flash(f"Welcome back, {user['username']}! Your tour research is ready.", "success")

        if next_url and next_url.startswith("/"):
            return redirect(next_url)
        return redirect(url_for("my_tour"))

    return render_template("login.html", answers={}, errors={}, next_url=next_url)


@app.route("/register", methods=["GET", "POST"])
def register():
    """User registration: Create an account to save tour planning research."""
    if session.get("username"):
        return redirect(url_for("my_tour"))

    if request.method == "POST":
        form_data = request.form.to_dict()
        is_valid, errors = validate_signup_form(form_data)

        if not is_valid:
            return render_template("register.html", answers=form_data, errors=errors), 400

        success, err_msg, new_user = register_user(
            username=form_data.get("username", ""),
            email=form_data.get("email", ""),
            password=form_data.get("password", ""),
        )

        if not success:
            return (
                render_template(
                    "register.html",
                    answers=form_data,
                    errors={"general": err_msg},
                ),
                400,
            )

        session.permanent = True
        session["username"] = new_user["username"]
        flash(f"Welcome to VibeTrip, {new_user['username']}! Your tour planning helper is active.", "success")
        return redirect(url_for("my_tour"))

    return render_template("register.html", answers={}, errors={})


@app.route("/logout")
def logout():
    """Clear session and log out the user."""
    user = session.pop("username", None)
    if user:
        flash("You have been logged out. See you on your next journey!", "info")
    return redirect(url_for("home"))


@app.route("/my-tour")
def my_tour():
    """Tour Planning Helper dashboard: Saved places wishlist, personal notes, and matched itineraries."""
    username = session.get("username")
    if not username:
        flash("Please log in to access your Tour Planning Helper dashboard.", "info")
        return redirect(url_for("login", next=url_for("my_tour")))

    profile = get_user_profile(username)
    saved_places = get_user_saved_places(username)
    saved_plans = get_user_saved_plans(username)

    return render_template(
        "my_tour.html",
        user_profile=profile,
        saved_places=saved_places,
        saved_plans=saved_plans,
    )


@app.route("/feedback", methods=["GET", "POST"])
def feedback():
    """Feedback form: Star rating, recommendation, and character-counted comments."""
    plan_id = request.args.get("plan", "").strip()

    if request.method == "POST":
        form_data = request.form.to_dict()
        is_valid, errors = validate_feedback_form(form_data)

        if not is_valid:
            return (
                render_template(
                    "feedback.html",
                    answers=form_data,
                    errors=errors,
                    plan_id=form_data.get("plan_id", ""),
                ),
                400,
            )

        append_feedback({
            "timestamp": get_now_iso(),
            "plan_id": form_data.get("plan_id", ""),
            "rating": form_data.get("rating", ""),
            "recommend": form_data.get("recommend", ""),
            "name": form_data.get("name", "").strip(),
            "comment": form_data.get("comment", "").strip(),
        })

        return render_template("feedback.html", submitted=True)

    return render_template("feedback.html", answers={}, errors={}, plan_id=plan_id, submitted=False)


@app.route("/contact", methods=["GET", "POST"])
def contact():
    """Contact page: Project contact details, SVG map, and message form."""
    if request.method == "POST":
        form_data = request.form.to_dict()
        is_valid, errors = validate_contact_form(form_data)

        if not is_valid:
            return render_template("contact.html", answers=form_data, errors=errors), 400

        append_contact({
            "timestamp": get_now_iso(),
            "name": form_data.get("name", "").strip(),
            "email": form_data.get("email", "").strip(),
            "message": form_data.get("message", "").strip(),
        })

        return render_template("contact.html", submitted=True)

    return render_template("contact.html", answers={}, errors={}, submitted=False)


@app.route("/lang/<code>")
def set_language(code: str):
    """Switch language between English ('en') and Nepali ('ne')."""
    if code in ["en", "ne"]:
        session["lang"] = code

    next_url = request.args.get("next")
    if next_url and next_url.startswith("/"):
        return redirect(next_url)

    referrer = request.referrer
    if referrer and request.host in referrer:
        return redirect(referrer)
    return redirect(url_for("home"))


@app.route("/api/vibes")
def api_vibes():
    """API endpoint returning vibes.json for dynamic JS use."""
    return jsonify(load_vibes())


@app.errorhandler(404)
def page_not_found(e):
    """Friendly 404 error page."""
    return render_template("404.html"), 404


@app.errorhandler(413)
def request_entity_too_large(e):
    """Handles oversized form posts (> 16 KB)."""
    flash("The submitted data was too large. Please shorten your response.", "error")
    return redirect(request.referrer or url_for("home"))


if __name__ == "__main__":
    app.run(debug=True, host="127.0.0.1", port=5000)
