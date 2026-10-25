"""
UX Specialist Integration & Client-Side Template Verification Tests.
Asserts that all functional UX breaks, event listener conflicts, broken links,
and interaction bindings are cleanly resolved across templates and scripts.
"""

import re
from pathlib import Path


def test_place_detail_wishlist_save_binding():
    main_js = Path("static/js/main.js").read_text(encoding="utf-8")
    place_html = Path("templates/place_detail.html").read_text(encoding="utf-8")

    # Ensure iconSpan and textSpan are declared
    assert "const iconSpan = savePlaceBtn.querySelector(\".save-icon\");" in main_js
    assert "const textSpan = savePlaceBtn.querySelector(\".save-text\");" in main_js
    
    # Ensure no duplicate full form submission fallback on caught exceptions
    assert "savePlaceForm.submit()" not in main_js

    # Ensure place_detail has matching IDs and class names
    assert 'id="savePlaceForm"' in place_html
    assert 'id="savePlaceBtn"' in place_html
    assert 'class="save-icon"' in place_html
    assert 'class="save-text"' in place_html


def test_results_page_event_deduplication():
    main_js = Path("static/js/main.js").read_text(encoding="utf-8")
    results_html = Path("templates/results.html").read_text(encoding="utf-8")
    results_js = Path("static/js/results.js").read_text(encoding="utf-8") if Path("static/js/results.js").exists() else ""
    results_content = results_html + results_js

    # In main.js, duplicate listeners for btnPrint, btnShare, and phrase-audio-btn must be removed
    assert 'document.getElementById("btnPrint")' not in main_js
    assert 'document.getElementById("btnShare")' not in main_js
    assert 'document.querySelectorAll(".phrase-audio-btn")' not in main_js

    # In results, btnPrint must call renderDayState('all') before window.print()
    assert "renderDayState('all')" in results_content
    assert "window.print()" in results_content

    # In results, btnShare must not clobber i18n text with hardcoded English
    assert 'shareBtnText.textContent = "Copied!"' not in results_content
    assert "navigator.clipboard.writeText" in results_content

    # In results, phrase-audio-btn must combine harmonic chime and SpeechSynthesis without canceling
    assert "audioButtons.forEach" in results_content
    assert "new AudioCtx()" in results_content or "new AudioContext()" in results_content
    assert "new SpeechSynthesisUtterance" in results_content


def test_quiz_q7_calendar_bypass():
    quiz_js = Path("static/js/quiz.js").read_text(encoding="utf-8")
    planner_html = Path("templates/planner.html").read_text(encoding="utf-8")

    # In quiz.js, check that steps with date pickers do not auto-advance immediately in 280ms
    assert "hasDatePickers" in quiz_js
    assert "if (!hasDatePickers)" in quiz_js

    # In planner.html, verify arrival and departure date fields and continue button
    assert 'id="startDateInput"' in planner_html
    assert 'id="endDateInput"' in planner_html
    assert 'btn-continue-calendar' in planner_html


def test_gemini_live_dom_updates():
    results_html = Path("templates/results.html").read_text(encoding="utf-8")
    results_js = Path("static/js/results.js").read_text(encoding="utf-8") if Path("static/js/results.js").exists() else ""
    results_content = results_html + results_js

    # Hero element IDs and live DOM update handles
    assert 'id="heroPersonaTagline"' in results_html
    assert 'id="heroPhilosophyText"' in results_html
    assert 'id="heroRhythmText"' in results_html
    assert 'id="heroGoldenRuleText"' in results_html

    # Ensure enhance callback updates all narrative targets
    assert "nar.bespoke_headline" in results_content
    assert "nar.local_rhythm_advice" in results_content
    assert "nar.golden_rule" in results_content
    assert "directiveCopyEl.textContent" in results_content
    assert "stop-monograph-why" in results_content


def test_gallery_monograph_links():
    gallery_html = Path("templates/gallery.html").read_text(encoding="utf-8")

    # Ensure places have direct links to place_detail monograph
    assert "url_for('place_detail', place_id=act.id)" in gallery_html
    assert "Read Monograph" in gallery_html


def test_my_tour_note_inputs_and_button_classes():
    my_tour_html = Path("templates/my_tour.html").read_text(encoding="utf-8")
    main_js = Path("static/js/main.js").read_text(encoding="utf-8")

    # Value must bind place.user_note rather than undefined user_research
    assert "value=\"{{ place.user_note or '' }}\"" in my_tour_html
    assert "user_research.notes" not in my_tour_html

    # Button classes must match between template and main.js
    assert "btn-dashboard-save-note" in my_tour_html
    assert "btn-save-inline-note" in my_tour_html
    assert ".btn-dashboard-save-note, .btn-save-inline-note" in main_js
