import { spawn } from 'node:child_process';

const proc = spawn('C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe', [
  '--headless=new',
  '--remote-debugging-port=9229',
  `--user-data-dir=${process.env.TEMP}\\debug_prof_eval3`,
  '--disable-gpu',
  '--window-size=1440,900',
  'http://127.0.0.1:5000/'
]);

setTimeout(async () => {
  try {
    const res = await fetch('http://127.0.0.1:9229/json/list');
    const targets = await res.json();
    const page = targets.find(t => t.type === 'page' && t.url.includes('5000'));
    if (page) {
      const ws = new WebSocket(page.webSocketDebuggerUrl);
      await new Promise(r => ws.onopen = r);

      // Check initial state
      let msgId = 1;
      function exec(expr) {
        return new Promise(resolve => {
          const id = msgId++;
          const handler = (e) => {
            const d = JSON.parse(e.data);
            if (d.id === id) {
              ws.removeEventListener('message', handler);
              resolve(d.result.result.value);
            }
          };
          ws.addEventListener('message', handler);
          ws.send(JSON.stringify({ id, method: 'Runtime.evaluate', params: { expression: expr, returnByValue: true } }));
        });
      }

      const initial = await exec(`(() => {
        const getR = el => el ? { top: el.getBoundingClientRect().top, bottom: el.getBoundingClientRect().bottom, height: el.getBoundingClientRect().height } : null;
        return {
          scrollH: document.documentElement.scrollHeight,
          innerH: window.innerHeight,
          navRect: getR(document.querySelector('.site-header')),
          navPos: window.getComputedStyle(document.querySelector('.site-header')).position,
          stageRect: getR(document.querySelector('#vibetour-stage')),
          homeMainRect: getR(document.querySelector('#home-main')),
        };
      })()`);
      console.log('Initial DOM:', initial);

      // Scroll to 1000
      await exec(`window.scrollTo(0, 1000)`);
      await new Promise(r => setTimeout(r, 400));

      const afterScroll = await exec(`(() => {
        const getR = el => el ? { top: el.getBoundingClientRect().top, bottom: el.getBoundingClientRect().bottom, height: el.getBoundingClientRect().height } : null;
        return {
          scrollY: window.scrollY,
          navRect: getR(document.querySelector('.site-header')),
          navClasses: document.querySelector('.site-header')?.className,
          stageRect: getR(document.querySelector('#vibetour-stage')),
          homeMainRect: getR(document.querySelector('#home-main')),
        };
      })()`);
      console.log('After scroll 1000:', afterScroll);

      // Capture screenshot after scroll
      const snap = await exec(`(() => { return true; })()`);
      const { spawnSync } = await import('node:child_process');
      const fs = await import('node:fs');
      ws.send(JSON.stringify({ id: 999, method: 'Page.captureScreenshot', params: { format: 'png' } }));
      await new Promise(resolve => {
        const h = (e) => {
          const d = JSON.parse(e.data);
          if (d.id === 999) {
            fs.writeFileSync('test_screens/scrolled_down_success.png', Buffer.from(d.result.data, 'base64'));
            console.log('Saved test_screens/scrolled_down_success.png');
            ws.removeEventListener('message', h);
            resolve();
          }
        };
        ws.addEventListener('message', h);
      });

      ws.close();
    }
  } catch (err) {
    console.error(err);
  } finally {
    proc.kill();
  }
}, 2000);
