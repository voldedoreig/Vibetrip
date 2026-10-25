import subprocess
import os
import sys
import time

CHROME_PATH = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
if not os.path.exists(CHROME_PATH):
    CHROME_PATH = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"

out_dir = os.path.abspath("test_screens")
os.makedirs(out_dir, exist_ok=True)

test_cases = [
    ("scene_01_mist_trail", "http://127.0.0.1:5000/?seek_t=3&paused=true"),
    ("scene_04_mountain_pass", "http://127.0.0.1:5000/?seek_t=28&paused=true"),
    ("scene_05_summit_sanctuary", "http://127.0.0.1:5000/?seek_t=44&paused=true"),
    ("scrolled_down_journal", "http://127.0.0.1:5000/?test_scroll=950"),
]

for name, url in test_cases:
    png_path = os.path.join(out_dir, f"{name}.png")
    temp_profile = os.path.join(os.environ.get("TEMP", "C:\\temp"), f"chrome_verify_{int(time.time()*1000)}")
    cmd = [
        CHROME_PATH,
        "--headless=new",
        f"--user-data-dir={temp_profile}",
        f"--screenshot={png_path}",
        "--window-size=1440,900",
        "--hide-scrollbars",
        "--disable-gpu",
        "--virtual-time-budget=2000",
        url
    ]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=20)
    print(f"Captured {name}: {os.path.exists(png_path)} ({os.path.getsize(png_path) if os.path.exists(png_path) else 0} bytes)")

print("All captures completed!")
