import subprocess
import time
import urllib.request
import os
import sys

PORT = 5059
BASE_URL = f"http://127.0.0.1:{PORT}"
CHROME_PATH = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
if not os.path.exists(CHROME_PATH):
    CHROME_PATH = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"

env = os.environ.copy()
env["FLASK_APP"] = "app.py"
server_proc = subprocess.Popen(
    ["uv", "run", "python", "-c", f"from app import app; app.run(port={PORT}, debug=False)"],
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    env=env
)

ready = False
for _ in range(25):
    time.sleep(0.5)
    try:
        with urllib.request.urlopen(f"{BASE_URL}/", timeout=1) as resp:
            if resp.status == 200:
                ready = True
                break
    except Exception:
        pass

if not ready:
    print("Server failed to respond.")
    server_proc.kill()
    sys.exit(1)

out_dir = os.path.abspath("test_screens")
os.makedirs(out_dir, exist_ok=True)

scroll_stages = [
    ("scroll_0", f"{BASE_URL}/?test_scroll=0"),
    ("scroll_800", f"{BASE_URL}/?test_scroll=800"),
    ("scroll_1800", f"{BASE_URL}/?test_scroll=1800"),
    ("scroll_3200", f"{BASE_URL}/?test_scroll=3200"),
]

for name, url in scroll_stages:
    png_path = os.path.join(out_dir, f"{name}.png")
    cmd = [
        CHROME_PATH,
        "--headless=new",
        f"--screenshot={png_path}",
        "--window-size=1440,900",
        "--hide-scrollbars",
        "--disable-gpu",
        url
    ]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=15)
    print(f"Captured {name}: {os.path.exists(png_path)} ({os.path.getsize(png_path) if os.path.exists(png_path) else 0} bytes)")

server_proc.terminate()
try:
    server_proc.wait(timeout=3)
except Exception:
    server_proc.kill()
print("All scroll tests finished!")
