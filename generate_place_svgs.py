"""Generates 10 scenic placeholder postcard SVGs for the VibeTrip intro."""

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
PLACES_DIR = BASE_DIR / "static" / "img" / "places"
PLACES_DIR.mkdir(parents=True, exist_ok=True)

PLACES = [
    {
        "file": "boudhanath.svg",
        "title": "Boudhanath Stupa",
        "sub": "Kathmandu, Nepal",
        "tag": "Spiritual Seeker",
        "icon": "",
        "c1": "#3B0764", "c2": "#7E22CE", "c3": "#E9D5FF"
    },
    {
        "file": "phewa_lake.svg",
        "title": "Phewa Lake",
        "sub": "Pokhara, Nepal",
        "tag": "Calm Explorer",
        "icon": "",
        "c1": "#064E3B", "c2": "#10B981", "c3": "#A7F3D0"
    },
    {
        "file": "holi_basantapur.svg",
        "title": "Holi Festival",
        "sub": "Basantapur, Nepal",
        "tag": "Festival Spark",
        "icon": "",
        "c1": "#881337", "c2": "#E11D48", "c3": "#FDE047"
    },
    {
        "file": "ebc_trail.svg",
        "title": "Everest Base Camp",
        "sub": "Himalayas, Nepal",
        "tag": "Adventure Seeker",
        "icon": "",
        "c1": "#0F172A", "c2": "#0284C7", "c3": "#BAE6FD"
    },
    {
        "file": "kyoto.svg",
        "title": "Kyoto Shrines",
        "sub": "Kyoto, Japan",
        "tag": "Heritage Historian",
        "icon": "",
        "c1": "#451A03", "c2": "#B45309", "c3": "#FDE68A"
    },
    {
        "file": "santorini.svg",
        "title": "Santorini Caldera",
        "sub": "Cyclades, Greece",
        "tag": "Calm Explorer",
        "icon": "",
        "c1": "#0C4A6E", "c2": "#0284C7", "c3": "#E0F2FE"
    },
    {
        "file": "rio_carnival.svg",
        "title": "Rio Carnival",
        "sub": "Rio de Janeiro, Brazil",
        "tag": "Festival Spark",
        "icon": "",
        "c1": "#4A044E", "c2": "#C026D3", "c3": "#FDE047"
    },
    {
        "file": "bangkok_food.svg",
        "title": "Street Food Night",
        "sub": "Bangkok, Thailand",
        "tag": "Foodie Wanderer",
        "icon": "",
        "c1": "#7C2D12", "c2": "#EA580C", "c3": "#FED7AA"
    },
    {
        "file": "swiss_alps.svg",
        "title": "Swiss Alpine Horn",
        "sub": "Valais, Switzerland",
        "tag": "Adventure Seeker",
        "icon": "",
        "c1": "#1E293B", "c2": "#0D9488", "c3": "#CCFBF1"
    },
    {
        "file": "marrakech.svg",
        "title": "Medina Souks",
        "sub": "Marrakech, Morocco",
        "tag": "Creative Soul",
        "icon": "",
        "c1": "#4C1D95", "c2": "#7C3AED", "c3": "#FBCFE8"
    }
]

for p in PLACES:
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 600" width="800" height="600">
  <defs>
    <linearGradient id="sky_{p['file'].replace('.', '_')}" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="{p['c1']}"/>
      <stop offset="60%" stop-color="{p['c2']}"/>
      <stop offset="100%" stop-color="{p['c3']}"/>
    </linearGradient>
    <filter id="shadow" x="-10%" y="-10%" width="120%" height="120%">
      <feDropShadow dx="0" dy="8" stdDeviation="12" flood-color="rgba(0,0,0,0.3)"/>
    </filter>
  </defs>
  <!-- Postcard Sky Background -->
  <rect width="800" height="600" fill="url(#sky_{p['file'].replace('.', '_')})"/>
  
  <!-- Scenic Silhouette Layers -->
  <path d="M0,420 Q200,360 400,410 T800,380 L800,600 L0,600 Z" fill="rgba(0,0,0,0.2)"/>
  <path d="M0,480 Q250,430 500,470 T800,440 L800,600 L0,600 Z" fill="rgba(0,0,0,0.3)"/>
  <circle cx="680" cy="140" r="60" fill="rgba(255,255,255,0.25)" filter="url(#shadow)"/>

  <!-- Postcard Stamp Aesthetic -->
  <rect x="30" y="30" width="740" height="540" fill="none" stroke="rgba(255,255,255,0.4)" stroke-width="2" stroke-dasharray="8 6"/>

  <!-- Centered Icon & Title -->
  <circle cx="400" cy="220" r="64" fill="rgba(255,255,255,0.22)" filter="url(#shadow)"/>
  <text x="400" y="244" font-size="64" text-anchor="middle" dominant-baseline="central">{p['icon']}</text>

  <rect x="280" y="315" width="240" height="32" rx="16" fill="rgba(0,0,0,0.35)"/>
  <text x="400" y="336" font-family="'Plus Jakarta Sans', system-ui, sans-serif" font-size="14" font-weight="700" fill="#FFFFFF" text-anchor="middle" letter-spacing="2">{p['tag'].upper()}</text>

  <text x="400" y="400" font-family="'Plus Jakarta Sans', system-ui, sans-serif" font-size="36" font-weight="800" fill="#FFFFFF" text-anchor="middle">{p['title']}</text>
  <text x="400" y="440" font-family="'Plus Jakarta Sans', system-ui, sans-serif" font-size="20" font-weight="600" fill="rgba(255,255,255,0.9)" text-anchor="middle"> {p['sub']}</text>
</svg>"""
    (PLACES_DIR / p["file"]).write_text(svg, encoding="utf-8")

print(f"Generated {len(PLACES)} place postcard SVGs successfully.")
