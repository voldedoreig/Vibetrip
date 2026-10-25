import { spawn } from "node:child_process";
import fs from "node:fs";

const CHROME = "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe";
const PORT = 9223;

const chromeProc = spawn(CHROME, [
  "--headless=new",
  `--remote-debugging-port=${PORT}`,
  "--remote-debugging-address=127.0.0.1",
  `--user-data-dir=${process.env.TEMP || "C:\\temp"}\\cdp_profile_${Date.now()}`,
  "--window-size=1440,900",
  "--disable-gpu",
  "--hide-scrollbars",
  "http://127.0.0.1:5000/"
]);

chromeProc.stderr.on("data", (d) => console.error("Chrome stderr:", d.toString()));
chromeProc.stdout.on("data", (d) => console.log("Chrome stdout:", d.toString()));
chromeProc.on("exit", (code) => console.log("Chrome exited with code", code));
async function waitReady() {
  for (let i = 0; i < 30; i++) {
    try {
      const res = await fetch(`http://127.0.0.1:${PORT}/json/list`);
      if (res.ok) {
        const list = await res.json();
        if (list.length > 0) return list[0];
      }
    } catch (e) {}
    await new Promise(r => setTimeout(r, 200));
  }
  throw new Error("Chrome CDP not ready");
}

async function run() {
  try {
    const pageTarget = await waitReady();
    const ws = new WebSocket(pageTarget.webSocketDebuggerUrl);

    let msgId = 1;
    const callbacks = new Map();

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (data.id && callbacks.has(data.id)) {
        callbacks.get(data.id)(data);
        callbacks.delete(data.id);
      }
      if (data.method === "Runtime.consoleAPICalled") {
        console.log("[Browser Console]", data.params.type, data.params.args.map(a => a.value));
      }
    };

    await new Promise(r => ws.onopen = r);

    function send(method, params = {}) {
      return new Promise((resolve) => {
        const id = msgId++;
        callbacks.set(id, resolve);
        ws.send(JSON.stringify({ id, method, params }));
      });
    }

    await send("Runtime.enable");
    await send("Page.enable");

    // Wait 1 sec for page load and intro init
    await new Promise(r => setTimeout(r, 1000));

    // Check DOM properties before scroll
    const evalResult0 = await send("Runtime.evaluate", {
      expression: `(() => {
        const container = document.getElementById("introContainer");
        const stage = document.getElementById("introStage");
        const world = document.getElementById("introWorld");
        const header = document.getElementById("introHeader");
        const cards = Array.from(document.querySelectorAll(".intro-postcard")).map((c, i) => ({
          idx: i,
          top: c.offsetTop,
          rect: c.getBoundingClientRect(),
          revealed: c.classList.contains("revealed"),
          opacity: window.getComputedStyle(c).opacity
        }));
        return {
          windowScrollY: window.scrollY,
          containerRect: container ? container.getBoundingClientRect() : null,
          stageRect: stage ? stage.getBoundingClientRect() : null,
          stagePosition: stage ? window.getComputedStyle(stage).position : null,
          worldRect: world ? world.getBoundingClientRect() : null,
          headerOpacity: header ? window.getComputedStyle(header).opacity : null,
          cards
        };
      })()`,
      returnByValue: true
    });

    console.log("=== STATE AT SCROLL 0 ===");
    console.log(JSON.stringify(evalResult0.result.value, null, 2));

    // Now simulate scrolling to 800px
    await send("Runtime.evaluate", {
      expression: `(() => {
        window.scrollTo(0, 800);
        window.dispatchEvent(new Event("scroll"));
      })()`
    });

    await new Promise(r => setTimeout(r, 500));

    const evalResult800 = await send("Runtime.evaluate", {
      expression: `(() => {
        const container = document.getElementById("introContainer");
        const stage = document.getElementById("introStage");
        const world = document.getElementById("introWorld");
        const header = document.getElementById("introHeader");
        const cards = Array.from(document.querySelectorAll(".intro-postcard")).map((c, i) => ({
          idx: i,
          top: c.offsetTop,
          rect: c.getBoundingClientRect(),
          revealed: c.classList.contains("revealed"),
          opacity: window.getComputedStyle(c).opacity
        }));
        return {
          windowScrollY: window.scrollY,
          containerRect: container ? container.getBoundingClientRect() : null,
          stageRect: stage ? stage.getBoundingClientRect() : null,
          stagePosition: stage ? window.getComputedStyle(stage).position : null,
          worldRect: world ? world.getBoundingClientRect() : null,
          worldTransform: world ? window.getComputedStyle(world).transform : null,
          headerOpacity: header ? window.getComputedStyle(header).opacity : null,
          cards
        };
      })()`,
      returnByValue: true
    });

    console.log("=== STATE AT SCROLL 800 ===");
    console.log(JSON.stringify(evalResult800.result.value, null, 2));

    // Capture screenshot at 800
    const snap = await send("Page.captureScreenshot", { format: "png" });
    fs.writeFileSync("test_screens/actual_scroll_800.png", Buffer.from(snap.result.data, "base64"));
    console.log("Saved test_screens/actual_scroll_800.png");

    ws.close();
  } finally {
    chromeProc.kill();
  }
}

run().catch(console.error);
