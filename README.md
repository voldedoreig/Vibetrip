# 🏔️ VibeTrip: Nepal Travel Consultation & Itinerary Engine

> **Personalized Travel Discovery & Cultural Monograph for Nepal and Kathmandu Valley**  
> Built with **Python 3.12, Flask, Vanilla JavaScript (ES6+), Semantic HTML5, and Modern CSS3**.  
> **100% Bilingual (English & Nepali Devanagari) • Zero SQL Database Required • Dual AI Engine (Gemini 2.5 Flash + Local Fallback)**

---

## 🌟 Overview

**VibeTrip** is an intelligent travel personalization web application designed to solve the two biggest problems in tourism planning:
1. **Generic, Rigid Timetables:** Locking travelers into unrealistic hour-by-hour itineraries that ignore traffic, fatigue, and spontaneous discovery.
2. **One-Size-Fits-All Tourist Checklists:** Forcing every traveler to visit the same famous spots regardless of whether they prefer quiet dawn monasteries, high-energy mountain climbs, spicy Newari feasts, or sacred river rituals.

By completing an intuitive **8-question consultation quiz**, travelers receive a tailored **"Split-Screen Field Dossier"** combining:
- A signature **Travel Persona** match calculated across a **7-Dimensional Personality Vector Space**.
- Authentic **5-Pillar Action Guidance** (first 30-minute directive, taste pairings, insider secrets, local etiquette, and transit directions).
- Active **Nepali cultural festivals** matched to travel dates using the traditional **Bikram Sambat (B.S.) lunar calendar**.
- An interactive **Split-Screen Scrollytelling Leaflet Map** synchronized to the traveler's scroll position.
- Native **Nepali and Newari audio phrasebooks** synthesized in real time via the browser's Web Audio API.
- A private **Traveler Dossier** (`/my-tour`) with bookmarking, personal field notes, and PDF export.

---

## 🚀 How to Start the Website

### Prerequisites
- **Python 3.10+** (Python 3.12 recommended)
- Windows, macOS, or Linux
- Terminal / PowerShell

---

### Method 1: 1-Click Windows Launcher (Easiest)

Simply double-click the **`start.bat`** file located in the project folder!  
It will automatically:
1. Detect your Python virtual environment.
2. Launch the Flask web server.
3. Automatically open your default web browser to **http://127.0.0.1:5000**.

---

### Method 2: Fast Command Line with `uv`

If you use the `uv` toolchain, run:

```powershell
uv run python app.py
```

The application will start immediately. Open your browser and navigate to:  
👉 **[http://127.0.0.1:5000](http://127.0.0.1:5000)**

---

### Method 3: Standard Python & Virtual Environment

1. **Clone or navigate to the project directory:**
   ```powershell
   cd "d:\bishesh\Code\Computer Project"
   ```

2. **Create and activate a virtual environment:**
   - **Windows (PowerShell):**
     ```powershell
     python -m venv .venv
     .\.venv\Scripts\activate
     ```
   - **macOS / Linux:**
     ```bash
     python3 -m venv .venv
     source .venv/bin/activate
     ```

3. **Install the dependencies:**
   ```powershell
   pip install -r requirements.txt
   ```
   *(Optional for AI generation: `pip install google-genai python-dotenv`)*

4. **Start the Flask server:**
   ```powershell
   python app.py
   ```

5. **Open your browser:**  
   👉 **[http://127.0.0.1:5000](http://127.0.0.1:5000)**

---

## 🔑 Pre-Seeded Test & Demo Accounts

For fast evaluation and grading, two accounts are pre-configured in the local JSON database:

| Account | Username | Email | Password | Role |
| :--- | :--- | :--- | :--- | :--- |
| **Creator Account** | `bishesh` | `bishesh2069@gmail.com` | `password123` | Primary Traveler Dossier |
| **Demo Account** | `demo_user_123` | `demo@example.com` | `password123` | Evaluator / Quick Testing |

> 💡 **Quick Fill:** On the `/login` page, you can simply click the **"Demo Traveler"** or **"Bishesh"** button to automatically populate credentials with one click!

---

## 🗺️ Key Website Pages & Navigation Routes

| Route | Description |
| :--- | :--- |
| **`/`** | **Expedition Journal Home**: Hand-drawn bamboo hero, animated intro, festival calendar preview, and valley monograph. |
| **`/planner`** | **8-Question Diagnostic Consultation**: Interactive quiz calculating travel archetype, duration (1–7 days), and expedition scope. |
| **`/results/<plan_id>`** | **Split-Screen Field Dossier**: Synchronized Leaflet map, day-by-day illustrated stops, 5 action pillars, and transit ribbons. |
| **`/gallery`** | **Illustrated Sanctuary Archive**: Real-time live search (English and Devanagari), vibe chips, and wishlist bookmarks. |
| **`/my-tour`** | **Traveler Dossier Dashboard**: Private saved sanctuaries, custom field notes, and past generated plans. |
| **`/login` & `/register`** | **Authentication System**: One-click demo autofill, password eye toggle, and persistent sessions. |
| **`/about`** | **Ethos & Methodology**: Information on the 7D personality space, scoring math, and cultural preservation. |
| **`/lang/en` & `/lang/ne`** | **Bilingual Toggle**: Instantly switches the entire website between English and Nepali. |

---

## 🧠 System Architecture & Personalization Engine

### 1. The 7-Dimensional Personality Vector Space
Every traveler profile, destination stop, and travel archetype is represented as a 7D coordinate vector:
$$\mathbf{P} = [\text{energy}, \text{crowd}, \text{culture}, \text{nature}, \text{food}, \text{spiritual}, \text{adventure}], \quad \text{where } P_i \in [0.0, 5.0]$$

### 2. Euclidean Distance Archetype Matching
The engine computes the **7D Euclidean distance** between the traveler's vector $\mathbf{P}$ and predefined target archetypes $\mathbf{V}$ (*Calm Explorer*, *Heritage Connoisseur*, *Foodie Wanderer*, *Spiritual Seeker*, etc.):
$$D(\mathbf{P}, \mathbf{V}) = \sqrt{\sum_{i=1}^{7} (P_i - V_i)^2}$$
Match affinity percentage:
$$\text{Match \%} = \max\left(0, \min\left(100, \text{round}\left(100 \times \left(1 - \frac{D(\mathbf{P}, \mathbf{V})}{\text{MAX\_DISTANCE}}\right)\right)\right)\right)$$

### 3. Multi-Constraint Slot Scheduling & Budget Relaxation
- Blends user answers with the matched persona using a $60/40$ ideal point formula:
  $$\mathbf{Ideal} = 0.60 \times \mathbf{Vibe}_{\text{target}} + 0.40 \times \mathbf{User}_{\text{profile}}$$
- Filters candidate stops by time slot suitability (*morning*, *afternoon*, *evening*), seasonal openings, and budget thresholds.
- If a budget traveler runs low on candidate spots, the algorithm automatically steps up the budget constraint rather than leaving an empty time slot.

### 4. Bikram Sambat (B.S.) Lunar Calendar Engine
- Converts Gregorian calendar dates to the traditional Nepali lunar calendar.
- Checks for active cultural events (*Indra Jatra*, *Bisket Jatra*, *Holi*, *Tihar*, *Maha Shivaratri*) and injects festival highlights directly into the daily itinerary.

### 5. Dual-Engine Narrative Synthesis (Gemini AI + Fallback)
- Connects to **Google Gemini 2.5 Flash API** to generate rich, personalized directives.
- Incorporates a **100% offline deterministic fallback synthesizer** so that itinerary generation never fails if the internet or API key is unavailable.

---

## 🛠️ Technology Stack & Languages

```
├── Python 3.12        -> Backend runtime, Flask controller, recommendation engine, auth
├── Vanilla JS (ES6+)  -> Multi-step quiz logic, live dossier preview, gallery search, scrollytelling
├── HTML5 / Jinja2     -> Semantic templates, partial inheritance, i18n localization filters
├── CSS3               -> Custom Lokta paper theme, CSS Grid/Flexbox, print stylesheets
├── Flat-File JSON     -> Zero-SQL database for users, research notes, sanctuaries, and plans
├── Leaflet.js         -> Interactive OpenStreetMap vector tiles & flyTo animations
└── Web Audio API      -> Native audio phrasebook synthesizer
```

---

## 🧪 Running Automated Tests

The application includes a comprehensive Pytest test suite covering route responses, scoring math, Bikram Sambat lunar conversions, user authentication, and UX workflows.

Run all tests from the root directory:

```powershell
uv run pytest tests
```
*or:*
```powershell
.venv\Scripts\python -m pytest tests
```

Expected result: **29 passed** in under 50 seconds.

---

## 📂 Project Directory Structure

```
├── app.py                     # Main Flask web application controller and route definitions
├── requirements.txt           # Python package dependencies
├── README.md                  # Master project documentation and startup guide
├── engine/                    # Core personalization and backend intelligence
│   ├── ai_generator.py        # Gemini 2.5 Flash API client & 5 action pillars generator
│   ├── auth.py                # Cryptographic authentication & dossier research management
│   ├── festivals.py           # Bikram Sambat (B.S.) lunar calendar and festival matcher
│   ├── i18n.py                # Bilingual translation engine (English & Nepali)
│   ├── itinerary.py           # Multi-day slot scheduler & budget constraint solver
│   ├── quiz.py                # Form input normalization & 7D trait vector builder
│   ├── recommendations.py     # Category and destination matching helpers
│   ├── scoring.py             # 7D Euclidean distance vector math calculations
│   ├── storage.py             # Flat-file JSON and CSV persistence helpers
│   ├── utils.py               # Date parsing and coordinate distance calculations
│   ├── validation.py          # Form input validation (quiz, login, signup, feedback)
│   └── vibes.py               # Travel persona classification and archetype definitions
├── data/                      # Lightweight file-based database
│   ├── places.json            # 10 major Nepal destinations & sanctuary monographs
│   ├── quiz_questions.json    # 8 consultation questions with full EN & NE translations
│   ├── vibes.json             # 8 travel archetype trait definitions
│   ├── users.json             # Salted password hash user records
│   ├── user_research.json     # Saved wishlists, plans, and field notes per user
│   ├── feedback.csv           # Traveler star ratings and reviews
│   ├── contact.csv            # Messages sent through the contact form
│   ├── i18n/                  # Dictionary files for bilingual text
│   │   ├── en.json            # English translations
│   │   └── ne.json            # Nepali Devanagari translations
│   └── plans/                 # Persisted JSON travel itineraries
├── static/                    # Frontend assets
│   ├── css/
│   │   ├── style.css          # Main stylesheet (Lokta paper & ink design system)
│   │   └── video_intro.css    # Cinematic video intro animations
│   ├── js/
│   │   ├── main.js            # Base navigation, theme toggle, and flash alerts
│   │   ├── quiz.js            # Multi-step quiz controller & live dossier updates
│   │   ├── gallery.js         # Instant search & live card filtering
│   │   ├── results.js         # Scrollytelling map controller & Web Audio player
│   │   ├── video_intro.js     # Canvas and SVG animated introduction
│   │   └── feedback.js        # Star rating widget and character counter
│   └── img/                   # Hand-drawn SVG illustrations & destination photos
├── templates/                 # Jinja2 HTML templates
│   ├── base.html              # Master layout with navigation and footer
│   ├── index.html             # Homepage and valley monograph
│   ├── planner.html           # 8-question travel consultation quiz
│   ├── results.html           # Split-screen scrollytelling itinerary dossier
│   ├── gallery.html           # Nepal sanctuary archive with live search
│   ├── my_tour.html           # Personal tour planning helper & wishlist dashboard
│   ├── login.html             # User login with one-click demo autofill
│   ├── register.html          # New traveler account registration
│   ├── about.html             # Project philosophy, methodology, and team ethos
│   ├── feedback.html          # Star rating and review submission
│   ├── contact.html           # Contact details and message form
│   └── partials/              # Reusable template components (navbar, footer, svgs)
└── tests/                     # Automated Pytest test suite
    ├── test_engine.py         # Unit tests for scoring, festivals, storage, and auth
    └── test_ux_specialist.py  # End-to-end integration and route response tests
```

---

## 📜 License & Academic Integrity

Created by **Bishesh Bhatt** for the **Grade 9 Computer Science Project (2025–2026)**.  
All code, algorithms, and design assets are structured for transparency, portability, and educational evaluation.
