import json
import os
import sys

sys.path.insert(0, os.getcwd())
from scripts.download_real_sanctuary_photos import TARGETS

ACTS_FILE = "data/destinations/nepal/activities.json"

with open(ACTS_FILE, "r", encoding="utf-8") as f:
    acts = json.load(f)

id_to_file = {t["id"]: f"/static/img/places/{t['file']}" for t in TARGETS}

updated_count = 0
for act in acts:
    a_id = act.get("id")
    if a_id in id_to_file:
        old_img = act.get("image")
        new_img = id_to_file[a_id]
        if old_img != new_img:
            act["image"] = new_img
            updated_count += 1
            print(f"Updated {a_id}: {old_img} -> {new_img}")

with open(ACTS_FILE, "w", encoding="utf-8") as f:
    json.dump(acts, f, indent=2, ensure_ascii=False)

print(f"\nUpdated {updated_count} activity image paths in {ACTS_FILE}")
