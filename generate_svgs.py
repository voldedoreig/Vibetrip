"""Utility script to generate vector SVG placeholders for vibes, activities, and map."""

import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

vibes_path = BASE_DIR / "data" / "vibes.json"
activities_path = BASE_DIR / "data" / "destinations" / "kathmandu" / "activities.json"

vibes = json.loads(vibes_path.read_text(encoding="utf-8"))
activities = json.loads(activities_path.read_text(encoding="utf-8"))

vibes_dir = BASE_DIR / "static" / "img" / "vibes"
activities_dir = BASE_DIR / "static" / "img" / "activities"

vibes_dir.mkdir(parents=True, exist_ok=True)
activities_dir.mkdir(parents=True, exist_ok=True)

# 1. Generate Vibe SVGs
for v in vibes:
    p = v["theme"]["primary"]
    a = v["theme"]["accent"]
    name = v["name"]
    icon = v["icon"]
    tagline = v["tagline"]

    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 500" width="800" height="500">
  <defs>
    <linearGradient id="bg" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="{p}"/>
      <stop offset="100%" stop-color="{a}"/>
    </linearGradient>
  </defs>
  <rect width="800" height="500" fill="url(#bg)"/>
  <circle cx="400" cy="220" r="180" fill="none" stroke="rgba(255,255,255,0.15)" stroke-width="2"/>
  <circle cx="400" cy="220" r="130" fill="none" stroke="rgba(255,255,255,0.25)" stroke-width="1.5" stroke-dasharray="6 6"/>
  
  <circle cx="400" cy="200" r="64" fill="rgba(255,255,255,0.2)"/>
  <text x="400" y="222" font-size="64" text-anchor="middle" dominant-baseline="central">{icon}</text>
  
  <text x="400" y="330" font-family="'Plus Jakarta Sans', system-ui, sans-serif" font-size="36" font-weight="800" fill="#FFFFFF" text-anchor="middle">{name}</text>
  <text x="400" y="375" font-family="'Plus Jakarta Sans', system-ui, sans-serif" font-size="18" font-weight="500" fill="rgba(255,255,255,0.85)" text-anchor="middle">{tagline[:55]}</text>
  <rect x="350" y="410" width="100" height="4" rx="2" fill="rgba(255,255,255,0.6)"/>
</svg>"""
    (vibes_dir / f"{v['id']}.svg").write_text(svg, encoding="utf-8")

# 2. Generate Activity SVGs
for act in activities:
    p = "#2D6A4F"
    a = "#52B788"
    icon = ""

    if act["traits"]["spiritual"] >= 4:
        p, a, icon = "#7E22CE", "#A855F7", ""
    elif act["traits"]["adventure"] >= 4:
        p, a, icon = "#EA580C", "#0D9488", ""
    elif act["traits"]["food"] >= 4:
        p, a, icon = "#C2410C", "#EAB308", ""
    elif act["traits"]["culture"] >= 5:
        p, a, icon = "#92400E", "#D97706", ""
    elif act["traits"]["crowd"] >= 5:
        p, a, icon = "#E11D48", "#F59E0B", ""
    elif act["traits"]["nature"] >= 4:
        p, a, icon = "#2D6A4F", "#52B788", ""

    name = act["name"]
    cat = act["category"]
    loc = act["location"]
    act_id = act["id"]

    line1 = name[:36]
    line2 = name[36:72]

    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 500" width="800" height="500">
  <defs>
    <linearGradient id="act_bg_{act_id}" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="{p}"/>
      <stop offset="100%" stop-color="{a}"/>
    </linearGradient>
  </defs>
  <rect width="800" height="500" fill="url(#act_bg_{act_id})"/>
  
  <path d="M0,380 Q200,320 400,360 T800,340 L800,500 L0,500 Z" fill="rgba(0,0,0,0.18)"/>
  <rect x="70" y="50" width="660" height="400" rx="24" fill="rgba(255,255,255,0.12)" stroke="rgba(255,255,255,0.28)" stroke-width="1.5"/>

  <circle cx="400" cy="150" r="50" fill="rgba(255,255,255,0.25)"/>
  <text x="400" y="168" font-size="52" text-anchor="middle" dominant-baseline="central">{icon}</text>

  <rect x="290" y="225" width="220" height="32" rx="16" fill="rgba(0,0,0,0.2)"/>
  <text x="400" y="246" font-family="'Plus Jakarta Sans', system-ui, sans-serif" font-size="14" font-weight="700" fill="#FFFFFF" text-anchor="middle" letter-spacing="1.5">{cat.upper()}</text>

  <text x="400" y="305" font-family="'Plus Jakarta Sans', system-ui, sans-serif" font-size="28" font-weight="800" fill="#FFFFFF" text-anchor="middle">{line1}</text>
  <text x="400" y="342" font-family="'Plus Jakarta Sans', system-ui, sans-serif" font-size="24" font-weight="800" fill="#FFFFFF" text-anchor="middle">{line2}</text>

  <text x="400" y="405" font-family="'Plus Jakarta Sans', system-ui, sans-serif" font-size="16" font-weight="600" fill="rgba(255,255,255,0.92)" text-anchor="middle"> {loc}</text>
</svg>"""
    (activities_dir / f"{act_id}.svg").write_text(svg, encoding="utf-8")

# 3. Generate Kathmandu Valley Map SVG
map_svg = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 500" width="800" height="500">
  <defs>
    <linearGradient id="map_bg" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#E2E8F0"/>
      <stop offset="100%" stop-color="#CBD5E1"/>
    </linearGradient>
  </defs>
  <rect width="800" height="500" fill="url(#map_bg)"/>
  
  <path d="M100,50 Q250,150 400,100 T700,80" fill="none" stroke="#94A3B8" stroke-width="4" stroke-dasharray="8 8"/>
  <path d="M50,220 Q200,180 380,240 T750,200" fill="none" stroke="#38BDF8" stroke-width="8" stroke-linecap="round"/>
  <text x="540" y="200" font-family="sans-serif" font-size="13" fill="#0284C7" font-weight="bold">Bagmati River</text>

  <path d="M120,400 Q320,320 520,380 T780,360" fill="none" stroke="#94A3B8" stroke-width="3" stroke-dasharray="6 6"/>

  <circle cx="340" cy="210" r="14" fill="#E11D48"/>
  <circle cx="340" cy="210" r="24" fill="none" stroke="#E11D48" stroke-width="2" opacity="0.5"/>
  <text x="340" y="185" font-family="sans-serif" font-size="15" font-weight="800" fill="#1E293B" text-anchor="middle">Thamel &amp; Durbar Sq</text>

  <circle cx="520" cy="150" r="12" fill="#7E22CE"/>
  <text x="520" y="130" font-family="sans-serif" font-size="13" font-weight="700" fill="#1E293B" text-anchor="middle">Boudhanath Stupa</text>

  <circle cx="220" cy="190" r="12" fill="#EA580C"/>
  <text x="220" y="170" font-family="sans-serif" font-size="13" font-weight="700" fill="#1E293B" text-anchor="middle">Swayambhunath</text>

  <circle cx="380" cy="330" r="12" fill="#2D6A4F"/>
  <text x="380" y="365" font-family="sans-serif" font-size="13" font-weight="700" fill="#1E293B" text-anchor="middle">Patan Durbar Square</text>

  <circle cx="660" cy="290" r="12" fill="#D97706"/>
  <text x="660" y="325" font-family="sans-serif" font-size="13" font-weight="700" fill="#1E293B" text-anchor="middle">Bhaktapur Old Town</text>

  <rect x="250" y="30" width="300" height="44" rx="22" fill="rgba(255,255,255,0.9)" stroke="#94A3B8"/>
  <text x="400" y="58" font-family="sans-serif" font-size="18" font-weight="800" fill="#0F172A" text-anchor="middle">Kathmandu Valley Map</text>
</svg>"""
(BASE_DIR / "static" / "img" / "kathmandu_map.svg").write_text(map_svg, encoding="utf-8")

print("All SVG placeholders generated successfully.")
