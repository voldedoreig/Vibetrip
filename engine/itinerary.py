"""Constructs the day-by-day itinerary plan for VibeTrip.

Balances vibe and traveler preferences, applies budget and seasonal filters,
integrates festival highlights, and ensures every slot is filled.
"""

import datetime
import secrets
from typing import Any, Dict, List, Optional, Set

from engine.ai_generator import (
    build_dna_pills,
    get_action_guidance_for_activity,
    personalize_itinerary_with_gemini,
)
from engine.festivals import find_festivals_for_trip, get_bs_date
from engine.recommendations import get_recommendations
from engine.scoring import (
    MAX_DISTANCE,
    compute_ideal_point,
    distance,
    haversine_distance_km,
)
from engine.storage import load_activities, save_plan
from engine.utils import get_now_iso, parse_date
from engine.vibes import choose_vibe

ALL_SLOTS = ["morning", "afternoon", "evening"]

# Geographic regions across Nepal and Kathmandu Valley to ensure cohesive day clustering
ACTIVITY_REGIONS: Dict[str, str] = {
    # Patan & South Lalitpur
    "patan_durbar_square": "patan_south",
    "woodcarving_patachitra_studio": "patan_south",
    "central_zoo_jawalakhel": "patan_south",
    "heritage_puppet_show": "patan_south",
    "godavari_botanical_gardens": "patan_south",

    # Central Kathmandu & Swayambhu / West
    "basantapur_durbar_square": "central_west",
    "asan_spice_bazaar": "central_west",
    "garden_of_dreams": "central_west",
    "thamel_food_walk": "central_west",
    "momo_cooking_class": "central_west",
    "thamel_live_music": "central_west",
    "indoor_climbing_adventure": "central_west",
    "swayambhunath_stupa": "central_west",
    "newari_feasting_kirtipur": "central_west",
    "chandragiri_cable_car": "central_west",
    "champadevi_ridge_trail": "central_west",

    # Bhaktapur & East Valley Rim / Boudha / Pashupati
    "bhaktapur_durbar_square": "east_rim",
    "taumadhi_pottery_square": "east_rim",
    "nagarkot_sunrise": "east_rim",
    "boudhanath_stupa": "east_rim",
    "thangka_art_workshop": "east_rim",
    "mandala_acoustic_jam": "east_rim",
    "pashupatinath_aarti": "east_rim",
    "kopan_monastery_meditation": "east_rim",
    "shivapuri_peak_hike": "east_rim",

    # Pokhara & Annapurna Lakes
    "phewa_lake_boating": "pokhara_valley",
    "world_peace_pagoda_pokhara": "pokhara_valley",
    "sarangkot_sunrise_viewpoint": "pokhara_valley",
    "begnas_lake_retreat": "pokhara_valley",
    "gupteshwor_cave_davis_fall": "pokhara_valley",
    "international_mountain_museum": "pokhara_valley",
    "poon_hill_ghorepani_trek": "annapurna_highlands",
    "annapurna_base_camp_sanctuary": "annapurna_highlands",
    "mardi_himal_ridge_trail": "annapurna_highlands",

    # Chitwan & Terai Wildlife
    "chitwan_jungle_safari": "chitwan_terai",
    "rapti_river_canoe_safari": "chitwan_terai",
    "tharu_cultural_village_walk": "chitwan_terai",
    "bardia_tiger_tracking_safari": "terai_wildlife",
    "suklaphanta_grassland_safari": "terai_wildlife",

    # Mustang & Trans-Himalayan Plateau
    "muktinath_temple_108_spouts": "mustang_plateau",
    "lo_manthang_walled_city": "mustang_plateau",
    "marpha_apple_village_walk": "mustang_plateau",
    "kagbeni_monastery_gateway": "mustang_plateau",

    # Lumbini & Sacred Birthplace
    "maya_devi_temple_lumbini": "lumbini_sacred",
    "lumbini_monastic_zone_walk": "lumbini_sacred",
    "tilaurakot_ancient_kapilavastu": "lumbini_sacred",

    # Everest / Khumbu Himalayas
    "namche_bazaar_sherpa_hub": "khumbu_everest",
    "tengboche_monastery_view": "khumbu_everest",
    "everest_base_camp_trek": "khumbu_everest",
    "kala_patthar_everest_sunrise": "khumbu_everest",
    "gokyo_lakes_and_ri": "khumbu_everest",

    # Langtang & Central Hills
    "kyanjin_gompa_cheese_factory": "langtang_valleys",
    "gosaikunda_sacred_alpine_lakes": "langtang_valleys",
    "bandipur_medieval_hill_town": "central_hills",
    "gorkha_historic_durbar": "central_hills",
    "rani_mahal_palpa": "central_hills",
    "tansen_dhaka_and_shrinagar": "central_hills",

    # Remote Lakes & Eastern Hills
    "rara_lake_national_park": "remote_wilderness",
    "shey_phoksundo_deep_blue_lake": "remote_wilderness",
    "khaptad_national_park_meadows": "remote_wilderness",
    "kanyam_tea_gardens_ilam": "eastern_hills",
    "sri_antu_kanchenjunga_sunrise": "eastern_hills",
    "janaki_mandir_janakpur": "eastern_hills",
    "vivaha_mandap_mithila_art": "eastern_hills",
    "pathibhara_devi_taplejung": "eastern_hills",
}

FESTIVAL_REGIONS: Dict[str, str] = {
    "basantapur_holi": "central_west",
    "ghode_jatra": "central_west",
    "bisket_jatra": "east_rim",
    "buddha_jayanti": "east_rim",
    "teej": "east_rim",
    "indra_jatra": "central_west",
    "dashain": "central_west",
    "tihar": "patan_south",
}


def get_vibe_region_order(vibe_target: Dict[str, float], activities: List[Dict[str, Any]]) -> List[str]:
    """Rank geographic regions by alignment with the traveler's vibe."""
    region_scores: Dict[str, List[float]] = {}
    for act in activities:
        reg = ACTIVITY_REGIONS.get(act.get("id", ""))
        if reg and "traits" in act:
            if reg not in region_scores:
                region_scores[reg] = []
            dist = distance(act["traits"], vibe_target)
            region_scores[reg].append(1.0 - (dist / MAX_DISTANCE))

    averages = {
        r: sum(scores) / len(scores) if scores else 0.5
        for r, scores in region_scores.items()
    }
    return sorted(averages.keys(), key=lambda r: -averages[r])


def score_activity(
    activity: Dict[str, Any],
    ideal: Dict[str, float],
    slot: str,
    preferred_slot: str,
    prev_activity: Optional[Dict[str, Any]] = None,
    day_region: Optional[str] = None,
    vibe_id: Optional[str] = None,
) -> float:
    """Calculate the match score for an activity against the ideal point.

    Base score: 1 - distance / MAX_DISTANCE.
    Applies bonuses for preferred slots and regional clustering.
    Applies penalties for distant stops and over-indexed activities.
    """
    dist = distance(activity["traits"], ideal)
    base_score = 1.0 - (dist / MAX_DISTANCE)
    if slot == preferred_slot:
        base_score += 0.05

    act_reg = ACTIVITY_REGIONS.get(activity.get("id", ""))
    if day_region and act_reg:
        base_score += 0.12 if act_reg == day_region else -0.20

    if prev_activity:
        prev_lat = prev_activity.get("lat")
        prev_lng = prev_activity.get("lng")
        if prev_lat is None or prev_lng is None:
            prev_id = prev_activity.get("id") or prev_activity.get("activity_id", "") or prev_activity.get("festival_id", "")
            prev_guide = get_action_guidance_for_activity(prev_id)
            prev_lat = prev_guide.get("lat", 27.7172)
            prev_lng = prev_guide.get("lng", 85.3240)

        act_lat = activity.get("lat")
        act_lng = activity.get("lng")
        if act_lat is None or act_lng is None:
            guide = get_action_guidance_for_activity(activity.get("id", ""))
            act_lat = guide.get("lat", 27.7172)
            act_lng = guide.get("lng", 85.3240)

        dist_km = haversine_distance_km(prev_lat, prev_lng, act_lat, act_lng)
        base_score -= min(0.30, dist_km * 0.02)

    if activity.get("id") == "heritage_puppet_show":
        if vibe_id not in ("family_fun", "creative_soul", "heritage_historian"):
            base_score -= 0.45

    return base_score


def pick_best_activity(
    activities: List[Dict[str, Any]],
    used_ids: Set[str],
    slot: str,
    budget_level: int,
    month: Optional[int],
    ideal: Dict[str, float],
    preferred_slot: str,
    prev_activity: Optional[Dict[str, Any]] = None,
    day_region: Optional[str] = None,
    vibe_id: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """Find the highest-scoring eligible activity for a slot, relaxing budget if needed."""
    for test_budget in range(budget_level, 4):
        eligible = []
        for act in activities:
            if act["id"] in used_ids:
                continue
            if slot not in act.get("slots", []):
                continue
            if act.get("cost_level", 1) > test_budget:
                continue
            act_months = act.get("months", [])
            if month is not None and act_months and month not in act_months:
                continue

            score = score_activity(
                act, ideal, slot, preferred_slot,
                prev_activity=prev_activity,
                day_region=day_region,
                vibe_id=vibe_id,
            )
            eligible.append((score, act, test_budget > budget_level))

        if eligible:
            eligible.sort(key=lambda item: (-item[0], item[1]["id"]))
            winner_score, winner_act, was_relaxed = eligible[0]
            return {
                "activity": winner_act,
                "score": winner_score,
                "relaxed_budget": was_relaxed,
            }

    return None


def _build_slot_entry(act: Dict[str, Any], guide: Dict[str, Any], relaxed_budget: bool) -> Dict[str, Any]:
    """Assemble a standard activity slot dictionary."""
    return {
        "activity_id": act["id"],
        "name": act["name"],
        "name_ne": act.get("name_ne"),
        "reason": guide.get("what_to_do"),
        "what_to_do": guide.get("what_to_do"),
        "taste_pairing": guide.get("taste_pairing"),
        "insider_secret": guide.get("insider_secret"),
        "etiquette_tip": guide.get("etiquette_tip"),
        "transit_tip": guide.get("transit_tip", "Walk through pedestrian bahals or take an electric taxi outside peak rush hour."),
        "ideal_window": guide.get("ideal_window"),
        "lat": guide.get("lat", 27.7172),
        "lng": guide.get("lng", 85.3240),
        "location": act.get("location", ""),
        "category": act.get("category", ""),
        "duration_hours": act.get("duration_hours", 2.0),
        "cost_level": act.get("cost_level", 1),
        "image": act.get("image", ""),
        "is_festival": False,
        "relaxed_budget": relaxed_budget,
    }


def _build_festival_slot(highlight: Dict[str, Any], guide: Dict[str, Any], slot: str, vibe_name: str) -> Dict[str, Any]:
    """Assemble a festival highlight slot dictionary."""
    return {
        "festival_id": highlight["festival_id"],
        "name": highlight["name"],
        "name_ne": highlight.get("name_ne"),
        "reason": f"Signature festival highlight for your {vibe_name} vibe. {guide.get('what_to_do')}",
        "what_to_do": guide.get("what_to_do"),
        "taste_pairing": guide.get("taste_pairing"),
        "insider_secret": guide.get("insider_secret"),
        "etiquette_tip": guide.get("etiquette_tip"),
        "transit_tip": guide.get("transit_tip", "Arrive early via walking approach; traffic restrictions apply around festival grounds."),
        "ideal_window": guide.get("ideal_window"),
        "lat": guide.get("lat", 27.7172),
        "lng": guide.get("lng", 85.3240),
        "location": highlight.get("location", "Kathmandu Valley"),
        "slot": slot,
        "is_festival": True,
        "verify_note": highlight.get("verify_note", ""),
    }


def _build_free_time_slot() -> Dict[str, Any]:
    """Assemble a fallback free-time slot dictionary."""
    return {
        "activity_id": "free_time",
        "name": "Courtyard Exploration & Spiced Tea",
        "name_ne": "बहाल भ्रमण र मसला चिया",
        "reason": "Wander the quiet residential bahals, listen to singing bowls, and sip fresh cardamom milk tea.",
        "what_to_do": "Wander without a fixed map through the sunlit residential courtyards (bahals) of Patan or Kathmandu. Peer into open workshops where woodcarvers chisel peacock struts.",
        "taste_pairing": "Order sweet spiced milk tea and warm crunchy sel roti from any neighborhood shop with a steaming cauldron.",
        "insider_secret": "Quiet courtyards often hide centuries-old stone chaityas and singing bowls not listed in guidebooks.",
        "etiquette_tip": "A simple 'Namaste' with hands folded will bring warm smiles from courtyard grandmothers.",
        "transit_tip": "Slow, contemplative walking through pedestrian residential courtyards.",
        "ideal_window": "Late afternoon (3:30 PM – 5:30 PM)",
        "lat": 27.7000,
        "lng": 85.3200,
        "location": "Kathmandu Valley",
        "category": "Relaxation",
        "duration_hours": 2.0,
        "cost_level": 1,
        "image": "/static/img/places/patan_durbar.jpg",
        "is_festival": False,
        "is_free_time": True,
    }


def generate_plan(
    profile: Dict[str, float],
    preferred_slot: str = "morning",
    budget_level: int = 2,
    days: int = 3,
    start_date: Optional[str] = None,
    destination: str = "kathmandu",
    timing_info: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Generate and persist a complete personalized recommendation plan."""
    winning_vibe, match_pct, runners_up = choose_vibe(profile)
    vibe_target = winning_vibe["target"]
    ideal = compute_ideal_point(vibe_target, profile)

    activities = load_activities(destination=destination)
    day_highlights, also_happening = find_festivals_for_trip(
        vibe_id=winning_vibe["id"],
        days=days,
        start_date=start_date,
    )

    start_dt = parse_date(start_date)
    plan_days: List[Dict[str, Any]] = []
    used_activity_ids: Set[str] = set()

    # Assign regional hub per day based on vibe ranking and scheduled festivals
    ordered_regions = get_vibe_region_order(vibe_target, activities)
    day_regions: Dict[int, str] = {}
    used_regions: Set[str] = set()

    for d_num in range(1, days + 1):
        hl = day_highlights.get(d_num)
        if hl:
            fest_reg = FESTIVAL_REGIONS.get(hl.get("festival_id", ""), "")
            if fest_reg:
                day_regions[d_num] = fest_reg
                used_regions.add(fest_reg)

    available_regions = [r for r in ordered_regions if r not in used_regions]
    for d_num in range(1, days + 1):
        if d_num not in day_regions:
            chosen_reg = (
                available_regions.pop(0)
                if available_regions
                else ordered_regions[(d_num - 1) % len(ordered_regions)]
            )
            day_regions[d_num] = chosen_reg

    for day_num in range(1, days + 1):
        day_date_str = None
        date_bs_str = None
        day_month = None
        current_day_region = day_regions.get(day_num, "central_west")

        if start_dt:
            current_day_dt = start_dt + datetime.timedelta(days=day_num - 1)
            day_date_str = current_day_dt.isoformat()
            date_bs_str = get_bs_date(current_day_dt)
            day_month = current_day_dt.month

        highlight_info = day_highlights.get(day_num)
        highlight_slot = highlight_info["slot"] if highlight_info else None

        slots_dict: Dict[str, Any] = {}
        prev_slot_activity: Optional[Dict[str, Any]] = None

        for slot in ALL_SLOTS:
            if highlight_info and slot == highlight_slot:
                fest_guide = get_action_guidance_for_activity(highlight_info.get("festival_id", ""))
                slots_dict[slot] = _build_festival_slot(highlight_info, fest_guide, slot, winning_vibe["name"])
                prev_slot_activity = slots_dict[slot]
                continue

            selection = pick_best_activity(
                activities=activities,
                used_ids=used_activity_ids,
                slot=slot,
                budget_level=budget_level,
                month=day_month,
                ideal=ideal,
                preferred_slot=preferred_slot,
                prev_activity=prev_slot_activity,
                day_region=current_day_region,
                vibe_id=winning_vibe["id"],
            )

            if selection:
                act = selection["activity"]
                used_activity_ids.add(act["id"])
                guide = get_action_guidance_for_activity(act["id"])
                slots_dict[slot] = _build_slot_entry(act, guide, selection["relaxed_budget"])
                prev_slot_activity = slots_dict[slot]
            else:
                slots_dict[slot] = _build_free_time_slot()

        plan_days.append({
            "day": day_num,
            "date": day_date_str,
            "date_bs": date_bs_str,
            "highlight": highlight_info,
            "slots": slots_dict,
        })

    active_timing = timing_info if timing_info else {
        "start_date": start_date if start_dt else None,
        "season": "flexible",
        "months": [start_dt.month] if start_dt else [],
    }

    rec_data = get_recommendations(
        profile=profile,
        preferred_slot=preferred_slot,
        budget_level=budget_level,
        timing_info=active_timing,
        destination=destination,
    )

    plan_id = secrets.token_hex(4)
    plan_data = {
        "id": plan_id,
        "created": get_now_iso(),
        "destination": destination,
        "vibe": winning_vibe["id"],
        "match_percent": match_pct,
        "runners_up": runners_up,
        "profile": profile,
        "raw_answers": profile.get("raw_answers", {}),
        "preferred_slot": preferred_slot,
        "budget_level": budget_level,
        "start_date": start_date if start_dt else None,
        "days": plan_days,
        "also_happening": also_happening,
        "timing_overview": rec_data["timing_overview"],
        "categories": rec_data["categories"],
        "grouped_places": rec_data["grouped_places"],
        "top_overall_highlights": rec_data["top_overall_highlights"],
        "festival_highlights": rec_data["festival_highlights"],
    }

    plan_data["dna_pills"] = build_dna_pills(plan_data, winning_vibe)
    plan_data = personalize_itinerary_with_gemini(plan_data)
    save_plan(plan_data)
    return plan_data
