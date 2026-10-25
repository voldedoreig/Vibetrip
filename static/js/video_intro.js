/**
 * VibeTourAnimation — 48-Second Sumi-e Ink-Wash & Non-Looping 1st-POV Trekking Journey
 *
 * Fixes included:
 * 1. Traveler Anatomy & Direction: Forward-leaning posture, extended front hand holding
 *    the trekking staff AHEAD of the body, alternating stride feet, and natural movement
 *    direction (walks right in Scenes 1–3 facing right; walks left up the summit ridge
 *    in Scene 5 facing left toward the sunrise).
 * 2. Non-Looping 1st-POV Mountain Pass (23.5s–33.5s): Zero modulo wrapping. 10 unique
 *    seeded mountain ridges pass once as you climb toward the summit tree rising ahead.
 */
class VibeTourAnimation {
  constructor(canvas, options = {}) {
    if (!canvas) throw new Error('VibeTourAnimation requires a valid HTMLCanvasElement.');
    this.canvas = canvas;
    this.ctx = canvas.getContext('2d');

    this.config = Object.assign({
      duration: 48.0,           // Tighter 48-second runtime (10s non-looping 1st-POV pass)
      keepAliveAtEnd: true,     // Keeps the final Summit Sunrise scene gently alive for the website hero
      seed: 1953,
      autoPlay: true,
      maxDPR: 2,
      onTimeUpdate: null,
      onSceneChange: null,
      onComplete: null
    }, options);

    this.width = 0;
    this.height = 0;
    this.dpr = 1;
    this.elapsed = 0;
    this.ambientTime = 0;
    this.isPlaying = false;
    this.hasCompleted = false;
    this.rafId = null;
    this.lastFrameTime = 0;
    this.currentSceneIndex = -1;

    this.scenes = [
      { id: 'beginning',   index: 0, label: '01 / The Mist Trail',        start: 0.0,  end: 8.0 },
      { id: 'hills',       index: 1, label: '02 / Terraced Hills',        start: 8.0,  end: 16.0 },
      { id: 'bamboo',      index: 2, label: '03 / Bamboo Forest',         start: 16.0, end: 23.5 },
      { id: 'pov_trek',    index: 3, label: '04 / 1st-POV Mountain Pass', start: 23.5, end: 33.5 },
      { id: 'destination', index: 4, label: '05 / Summit Sanctuary',      start: 33.5, end: 48.0 }
    ];

    this._initInkWorld();

    this._boundResize = this.resize.bind(this);
    this._boundTick = this._tick.bind(this);

    window.addEventListener('resize', this._boundResize);
    this.resize();

    if (this.config.autoPlay) {
      this.play();
    } else {
      this.render(0, 0);
    }
  }

  /* --- MATH & COLOR INTERPOLATION HELPERS --- */
  _createPRNG(seed) {
    let s = seed % 2147483647;
    if (s <= 0) s += 2147483646;
    return () => {
      s = (s * 16807) % 2147483647;
      return (s - 1) / 2147483646;
    };
  }

  _lerp(a, b, t) {
    return a + (b - a) * t;
  }

  _clamp(v, min = 0, max = 1) {
    return Math.max(min, Math.min(max, v));
  }

  _smoothstep(edge0, edge1, x) {
    const t = this._clamp((x - edge0) / (edge1 - edge0), 0, 1);
    return t * t * (3 - 2 * t);
  }

  _hexToRgb(hex) {
    const clean = hex.replace('#', '');
    const num = parseInt(clean, 16);
    return {
      r: (num >> 16) & 255,
      g: (num >> 8) & 255,
      b: num & 255
    };
  }

  _lerpColor(hexA, hexB, t, alpha = 1) {
    const c = this._clamp(t, 0, 1);
    const a = this._hexToRgb(hexA);
    const b = this._hexToRgb(hexB);
    const r = Math.round(this._lerp(a.r, b.r, c));
    const g = Math.round(this._lerp(a.g, b.g, c));
    const bl = Math.round(this._lerp(a.b, b.b, c));
    return alpha < 1 ? `rgba(${r}, ${g}, ${bl}, ${alpha})` : `rgb(${r}, ${g}, ${bl})`;
  }

  /* --- DETERMINISTIC SUMI-E WORLD INITIALIZATION --- */
  _initInkWorld() {
    const rand = this._createPRNG(this.config.seed);

    // 1. Parabolic Ink-Wash Mountains (Scenes 1–3)
    this.backInkPeaks = [
      { x: -0.05, w: 0.16, h: 0.42 },
      { x: 0.20,  w: 0.11, h: 0.72 },
      { x: 0.45,  w: 0.14, h: 0.55 },
      { x: 0.70,  w: 0.12, h: 0.76 },
      { x: 0.96,  w: 0.15, h: 0.60 },
      { x: 1.18,  w: 0.14, h: 0.48 }
    ];

    this.midInkPeaks = [
      { x: 0.08,  w: 0.15, h: 0.34 },
      { x: 0.37,  w: 0.14, h: 0.38 },
      { x: 0.61,  w: 0.16, h: 0.44 },
      { x: 0.86,  w: 0.15, h: 0.36 },
      { x: 1.10,  w: 0.15, h: 0.32 }
    ];

    this.nearHillPeaks = [
      { x: 0.12, w: 0.22, h: 0.22 },
      { x: 0.48, w: 0.25, h: 0.25 },
      { x: 0.85, w: 0.24, h: 0.21 },
      { x: 1.20, w: 0.22, h: 0.23 }
    ];

    // 2. Bamboo Forest Stalks (Scene 3)
    this.bambooStalks = [
      { x: 0.09, width: 10, depth: 0, alpha: 0.18, nodes: 6, lean: 0.01, seed: 1 },
      { x: 0.24, width: 12, depth: 0, alpha: 0.22, nodes: 7, lean: -0.015, seed: 2 },
      { x: 0.41, width: 9,  depth: 0, alpha: 0.16, nodes: 6, lean: 0.01, seed: 3 },
      { x: 0.63, width: 11, depth: 0, alpha: 0.20, nodes: 7, lean: -0.01, seed: 4 },
      { x: 0.84, width: 12, depth: 0, alpha: 0.22, nodes: 6, lean: 0.012, seed: 5 },
      { x: 0.15, width: 16, depth: 1, alpha: 0.42, nodes: 6, lean: 0.008, seed: 6 },
      { x: 0.52, width: 15, depth: 1, alpha: 0.38, nodes: 6, lean: -0.012, seed: 7 },
      { x: 0.91, width: 17, depth: 1, alpha: 0.45, nodes: 6, lean: 0.01, seed: 8 },
      { x: 0.05, width: 24, depth: 2, alpha: 0.85, nodes: 5, lean: 0.005, seed: 9 },
      { x: 0.77, width: 25, depth: 2, alpha: 0.88, nodes: 5, lean: -0.006, seed: 10 },
      { x: 0.96, width: 22, depth: 2, alpha: 0.82, nodes: 5, lean: -0.01, seed: 11 }
    ];

    // 3. Unique Non-Looping 1st-POV Mountain Ridges (10 distinct pairs along the climb)
    // Each ridge has a fixed zStart along the pass so none ever loop or repeat!
    this.povMountainPairs = Array.from({ length: 10 }, (_, idx) => ({
      id: idx,
      // Spaced from z = 0.12 (near start) to z = 1.65 (high pass summit)
      initialZ: 0.15 + idx * 0.165,
      leftHeight: 0.24 + rand() * 0.28,
      rightHeight: 0.22 + rand() * 0.30,
      leftTwinPeak: idx % 2 === 0,
      rightTwinPeak: idx % 3 === 0,
      leftSharpness: 0.35 + rand() * 0.45,
      rightSharpness: 0.35 + rand() * 0.45,
      leftSpreadOffset: (rand() - 0.5) * 0.08,
      rightSpreadOffset: (rand() - 0.5) * 0.08,
      hasPineSilhouette: idx < 6,
      tintShift: rand()
    }));

    // 4. Grand Finale Sanctuary Blossom Tree (Scene 5)
    this.summitTree = this._generateSummitSanctuaryTree(rand);

    // 5. Drifting Blossom Petals & Ink Leaves
    this.floatingParticles = Array.from({ length: 38 }, (_, i) => ({
      x: rand(),
      y: rand(),
      speedX: -0.022 - rand() * 0.03,
      speedY: 0.010 + rand() * 0.02,
      size: 4.5 + rand() * 6,
      angle: rand() * Math.PI * 2,
      spin: (rand() - 0.5) * 2.0,
      type: i % 3 === 0 ? 'bambooLeaf' : 'petal',
      depth: rand()
    }));

    // 6. Calligraphic Grass Tufts
    this.inkGrass = Array.from({ length: 28 }, () => ({
      x: rand(),
      blades: 2 + Math.floor(rand() * 3),
      height: 10 + rand() * 14,
      phase: rand() * Math.PI * 2
    }));

    // 7. Subtle Rice-Paper Fiber Texture
    this.paperFibers = Array.from({ length: 65 }, () => ({
      x: rand(),
      y: rand(),
      len: 8 + rand() * 22,
      angle: rand() * Math.PI,
      alpha: 0.03 + rand() * 0.04
    }));

    // 8. Summit Sea of Clouds & Soaring Birds
    this.summitCloudRibbons = Array.from({ length: 12 }, (_, i) => ({
      x: (i / 12) * 1.4 - 0.2,
      y: 0.64 + (i % 4) * 0.045,
      w: 0.28 + rand() * 0.25,
      h: 0.026 + rand() * 0.02,
      speed: (0.006 + rand() * 0.006) * (i % 2 === 0 ? 1 : -0.7),
      alpha: 0.35 + rand() * 0.35
    }));

    this.summitBirds = Array.from({ length: 7 }, (_, i) => ({
      x: 0.15 + i * 0.07,
      y: 0.26 + (i % 3) * 0.04,
      speedX: 0.012 + rand() * 0.005,
      phase: rand() * Math.PI * 2
    }));
  }

  _generateSummitSanctuaryTree(rand) {
    const segments = [
      { x1: 0.0,   y1: 0.0,   cx: -0.05, cy: -0.18, x2: -0.13, y2: -0.35, w1: 36, w2: 25 },
      { x1: -0.13, y1: -0.35, cx: -0.26, cy: -0.48, x2: -0.44, y2: -0.56, w1: 24, w2: 14 },
      { x1: -0.44, y1: -0.56, cx: -0.58, cy: -0.62, x2: -0.74, y2: -0.59, w1: 14, w2: 4 },
      { x1: -0.58, y1: -0.60, cx: -0.68, cy: -0.69, x2: -0.80, y2: -0.70, w1: 7,  w2: 2 },
      { x1: -0.13, y1: -0.35, cx: -0.16, cy: -0.56, x2: -0.22, y2: -0.78, w1: 18, w2: 6 },
      { x1: -0.18, y1: -0.58, cx: -0.30, cy: -0.70, x2: -0.45, y2: -0.76, w1: 11, w2: 3 },
      { x1: -0.09, y1: -0.24, cx: -0.28, cy: -0.28, x2: -0.50, y2: -0.25, w1: 15, w2: 3.5 },
      { x1: -0.30, y1: -0.27, cx: -0.40, cy: -0.36, x2: -0.54, y2: -0.38, w1: 9,  w2: 2.5 },
      { x1: -0.07, y1: -0.28, cx: 0.01,  cy: -0.45, x2: 0.08,  y2: -0.64, w1: 12, w2: 3 },
      { x1: -0.01, y1: -0.01, cx: -0.07, cy: 0.04,  x2: -0.14, y2: 0.06,  w1: 14, w2: 3 },
      { x1: 0.01,  y1: -0.01, cx: 0.05,  cy: 0.03,  x2: 0.09,  y2: 0.06,  w1: 12, w2: 3 }
    ];

    const anchors = [
      [-0.74, -0.59], [-0.67, -0.60], [-0.80, -0.70], [-0.72, -0.68],
      [-0.58, -0.60], [-0.50, -0.58], [-0.44, -0.56], [-0.36, -0.52],
      [-0.45, -0.76], [-0.37, -0.73], [-0.29, -0.69], [-0.22, -0.78],
      [-0.19, -0.68], [-0.50, -0.25], [-0.42, -0.26], [-0.34, -0.27],
      [-0.54, -0.38], [-0.46, -0.37], [-0.38, -0.33], [-0.25, -0.43],
      [-0.32, -0.46], [0.08, -0.64],  [0.03, -0.54],  [-0.02, -0.46]
    ];

    const blossoms = [];
    anchors.forEach(([ax, ay]) => {
      for (let k = 0; k < 3; k++) {
        blossoms.push({
          x: ax + (rand() - 0.5) * 0.055,
          y: ay + (rand() - 0.5) * 0.045,
          r: 7.5 + rand() * 5.5,
          phase: rand() * Math.PI * 2
        });
      }
    });

    return { segments, blossoms };
  }

  /* --- SCENE TIMELINE WEIGHTS (48 SECONDS) --- */
  _getSceneWeights(t) {
    const hillsPresence = this._smoothstep(6.5, 10.0, t) * (1.0 - this._smoothstep(14.5, 17.5, t));
    const bambooPresence = this._smoothstep(14.5, 17.5, t) * (1.0 - this._smoothstep(22.0, 25.0, t));

    // Camera zoom-in right before transitioning into 1st-POV Trekking (21.5s -> 24.8s)
    const prePovZoom = this._smoothstep(21.5, 24.8, t) * (1.0 - this._smoothstep(24.8, 26.0, t));

    // Scene 4: Non-looping 1st-POV Mountain Pass Trek (23.2s -> 34.5s)
    const povWeight = this._smoothstep(23.2, 25.5, t) * (1.0 - this._smoothstep(32.5, 35.2, t));

    // Scene 5: Grand Finale Summit Sanctuary beside the Tree at Sunrise/Sunset (32.5s -> 48.0s)
    const summitWeight = this._smoothstep(32.5, 35.8, t);
    const sunriseGlory = this._smoothstep(33.5, 41.5, t);

    const sideTravelerAlpha = 1.0 - this._smoothstep(23.0, 25.0, t);

    return {
      hillsPresence,
      bambooPresence,
      prePovZoom,
      povWeight,
      summitWeight,
      sunriseGlory,
      sideTravelerAlpha
    };
  }

  /* --- MAIN RENDER PIPELINE --- */
  render(t = this.elapsed, ambientT = this.ambientTime) {
    const ctx = this.ctx;
    const w = this.width;
    const h = this.height;
    if (!w || !h) return;

    const weights = this._getSceneWeights(t);
    const camScroll = t / this.config.duration;

    // ------------------------------------------------------------------------
    // PHASE A: SIDE-SCROLLING SUMI-E JOURNEY (Scenes 1, 2, 3: 0s – 25s)
    // ------------------------------------------------------------------------
    if (weights.summitWeight < 0.99 && weights.povWeight < 0.99) {
      ctx.save();

      const zoomFactor = 1.0 + weights.prePovZoom * 0.65;
      ctx.translate(w * 0.48, h * 0.72);
      ctx.scale(zoomFactor, zoomFactor);
      ctx.translate(-w * 0.48, -h * 0.72);

      this._drawParchmentAndSun(ctx, w, h, t, weights);
      this._drawInkWashMountains(ctx, w, h, t, camScroll, weights);

      if (weights.hillsPresence > 0.01) {
        this._drawInkTerracedHills(ctx, w, h, t, camScroll, weights);
      }

      if (weights.bambooPresence > 0.01) {
        this._drawBambooLayer(ctx, w, h, ambientT, weights.bambooPresence, [0, 1]);
      }

      this._drawInkSlopeAndTraveler(ctx, w, h, t, ambientT, weights);

      if (weights.bambooPresence > 0.01) {
        this._drawBambooLayer(ctx, w, h, ambientT, weights.bambooPresence, [2]);
      }

      ctx.restore();
    }

    // ------------------------------------------------------------------------
    // PHASE B: NON-LOOPING 1ST-POV MOUNTAIN PASS TREK (Scene 4: 23.5s – 34.5s)
    // ------------------------------------------------------------------------
    if (weights.povWeight > 0.01) {
      this._drawFirstPersonTrekScene(ctx, w, h, t, ambientT, weights.povWeight);
    }

    // ------------------------------------------------------------------------
    // PHASE C: GRAND FINALE SUMMIT SANCTUARY & SUNRISE/SUNSET (Scene 5: 33s – 48s+)
    // ------------------------------------------------------------------------
    if (weights.summitWeight > 0.01) {
      this._drawSummitSanctuaryMasterpiece(ctx, w, h, t, ambientT, weights);
    }

    // Global Drifting Blossoms & Rice-Paper Scroll Vignette
    this._drawFloatingInkParticles(ctx, w, h, ambientT, weights);
    this._drawScrollVignette(ctx, w, h, t);
  }

  /* --- PHASE A HELPERS (SCENES 1–3) --- */
  _drawParchmentAndSun(ctx, w, h, t, weights) {
    const { bambooPresence } = weights;

    const topColor = this._lerpColor('#E5DDD0', '#B5AEA0', bambooPresence * 0.7);
    const bottomColor = this._lerpColor('#F2ECE1', '#DDD6C7', bambooPresence * 0.6);

    const bgGrad = ctx.createLinearGradient(0, 0, 0, h);
    bgGrad.addColorStop(0, topColor);
    bgGrad.addColorStop(1, bottomColor);
    ctx.fillStyle = bgGrad;
    ctx.fillRect(0, 0, w, h);

    this._drawPaperFibers(ctx, w, h);

    const orbX = w * 0.74;
    const orbY = h * 0.24;
    const orbRadius = Math.min(w, h) * 0.14;

    ctx.beginPath();
    ctx.arc(orbX, orbY, orbRadius, 0, Math.PI * 2);
    ctx.fillStyle = '#FAF5E8';
    ctx.fill();
  }

  _drawPaperFibers(ctx, w, h) {
    ctx.save();
    ctx.strokeStyle = '#3A3630';
    ctx.lineWidth = 0.8;
    this.paperFibers.forEach((f) => {
      ctx.globalAlpha = f.alpha;
      const fx = f.x * w;
      const fy = f.y * h;
      ctx.beginPath();
      ctx.moveTo(fx, fy);
      ctx.lineTo(fx + Math.cos(f.angle) * f.len, fy + Math.sin(f.angle) * f.len);
      ctx.stroke();
    });
    ctx.restore();
  }

  _drawInkWashMountains(ctx, w, h, t, camScroll, weights) {
    const mountainAlpha = 1.0 - weights.bambooPresence * 0.55;
    const baseY = h * 0.82;

    this._renderInkMountainRange(ctx, w, h, {
      peaks: this.backInkPeaks,
      baseY: baseY,
      heightScale: 0.92,
      scrollOffset: 0,
      inkTopColor: '#C9C2B4',
      inkOutlineColor: '#787267',
      paperFadeColor: '#EFE9DC',
      alpha: mountainAlpha
    });

    this._renderInkMountainRange(ctx, w, h, {
      peaks: this.midInkPeaks,
      baseY: baseY + h * 0.06,
      heightScale: 0.80,
      scrollOffset: 0,
      inkTopColor: '#BDB5A6',
      inkOutlineColor: '#5C574F',
      paperFadeColor: '#F2ECE1',
      alpha: mountainAlpha * 0.95
    });
  }

  _renderInkMountainRange(ctx, w, h, opts) {
    const {
      peaks, baseY, heightScale, scrollOffset,
      inkTopColor, inkOutlineColor, paperFadeColor, alpha
    } = opts;

    ctx.save();
    ctx.globalAlpha = alpha;

    const steps = 180;
    const pts = [];
    let minY = h;

    for (let i = 0; i <= steps; i++) {
      const nx = i / steps;
      const px = nx * w;
      const sampleX = nx + scrollOffset;

      let elev = 0;
      for (let p = 0; p < peaks.length; p++) {
        const pk = peaks[p];
        const dx = (sampleX - pk.x) / pk.w;
        // Jagged Himalayan crest formula: sharp pyramid ridges with rock facet cuts
        const sharpPeak = Math.exp(-Math.abs(dx) * 2.5) * (1.0 - Math.abs(Math.sin(dx * 5.2)) * 0.16) * pk.h;
        elev = Math.max(elev, sharpPeak);
      }

      const handWave = Math.sin(sampleX * 18) * 0.005 + Math.cos(sampleX * 9) * 0.007;
      const py = baseY - (elev + handWave) * h * heightScale;
      if (py < minY) minY = py;
      pts.push({ x: px, y: py });
    }

    ctx.beginPath();
    ctx.moveTo(0, h);
    for (let i = 0; i <= steps; i++) ctx.lineTo(pts[i].x, pts[i].y);
    ctx.lineTo(w, h);
    ctx.closePath();

    const washGrad = ctx.createLinearGradient(0, minY, 0, baseY);
    washGrad.addColorStop(0, inkTopColor);
    washGrad.addColorStop(0.62, this._lerpColor(inkTopColor, paperFadeColor, 0.55));
    washGrad.addColorStop(0.95, paperFadeColor);
    washGrad.addColorStop(1, paperFadeColor);

    ctx.fillStyle = washGrad;
    ctx.fill();

    ctx.beginPath();
    for (let i = 0; i <= steps; i++) {
      if (i === 0) ctx.moveTo(pts[i].x, pts[i].y);
      else ctx.lineTo(pts[i].x, pts[i].y);
    }
    ctx.strokeStyle = inkOutlineColor;
    ctx.lineWidth = 7.0;
    ctx.lineCap = 'round';
    ctx.lineJoin = 'round';
    ctx.globalAlpha = alpha * 0.16;
    ctx.stroke();

    ctx.lineWidth = 2.2;
    ctx.globalAlpha = alpha * 0.48;
    ctx.stroke();

    ctx.restore();
  }

  _drawInkTerracedHills(ctx, w, h, t, camScroll, weights) {
    ctx.save();
    ctx.globalAlpha = weights.hillsPresence;

    const steps = 120;
    const pts = [];
    const baseY = h * 0.80;

    for (let i = 0; i <= steps; i++) {
      const nx = i / steps;
      const px = nx * w;
      const sampleX = nx;
      let elev = 0;
      this.nearHillPeaks.forEach((pk) => {
        const dx = (sampleX - pk.x) / pk.w;
        elev = Math.max(elev, Math.exp(-dx * dx * 2.0) * pk.h);
      });
      const py = baseY - elev * h;
      pts.push({ x: px, y: py });
    }

    ctx.beginPath();
    ctx.moveTo(0, h);
    pts.forEach((p) => ctx.lineTo(p.x, p.y));
    ctx.lineTo(w, h);
    ctx.closePath();

    const hillGrad = ctx.createLinearGradient(0, h * 0.52, 0, baseY);
    hillGrad.addColorStop(0, 'rgba(122, 134, 116, 0.65)');
    hillGrad.addColorStop(1, 'rgba(242, 236, 225, 0.1)');
    ctx.fillStyle = hillGrad;
    ctx.fill();

    ctx.strokeStyle = 'rgba(72, 78, 68, 0.35)';
    for (let tier = 1; tier <= 4; tier++) {
      ctx.lineWidth = 2.2 - tier * 0.3;
      ctx.beginPath();
      for (let i = 15; i < steps - 15; i++) {
        const p = pts[i];
        const ty = p.y + tier * 14 + Math.sin(i * 0.2 + tier) * 2;
        if (i === 15) ctx.moveTo(p.x, ty);
        else ctx.lineTo(p.x, ty);
      }
      ctx.stroke();
    }

    ctx.restore();
  }

  _drawBambooLayer(ctx, w, h, ambientT, presence, allowedDepths) {
    ctx.save();

    this.bambooStalks.forEach((stalk) => {
      if (!allowedDepths.includes(stalk.depth)) return;

      const parallax = (stalk.depth + 1) * 0.035 * (ambientT - 15.0);
      const normX = ((stalk.x - parallax) % 1.15 + 1.15) % 1.15 - 0.07;
      const baseX = normX * w;
      const sway = Math.sin(ambientT * 1.1 + stalk.seed) * (4 + stalk.depth * 3);

      ctx.globalAlpha = presence * stalk.alpha;

      const segHeight = h / stalk.nodes;
      const stalkW = stalk.width * (Math.min(w, 1400) / 1200);

      for (let n = 0; n < stalk.nodes; n++) {
        const yBottom = h - n * segHeight;
        const yTop = yBottom - segHeight + 4;
        const xBottom = baseX + (n * stalk.lean * w) + sway * (n / stalk.nodes);
        const xTop = baseX + ((n + 1) * stalk.lean * w) + sway * ((n + 1) / stalk.nodes);

        ctx.strokeStyle = '#1E1D1A';
        ctx.lineWidth = stalkW;
        ctx.lineCap = 'butt';
        ctx.beginPath();
        ctx.moveTo(xBottom, yBottom);
        ctx.lineTo(xTop, yTop);
        ctx.stroke();

        ctx.strokeStyle = '#B8B0A0';
        ctx.lineWidth = stalkW * 0.28;
        ctx.beginPath();
        ctx.moveTo(xBottom - stalkW * 0.12, yBottom - 4);
        ctx.lineTo(xTop - stalkW * 0.12, yTop + 4);
        ctx.stroke();

        ctx.strokeStyle = '#141311';
        ctx.lineWidth = 3.2;
        ctx.lineCap = 'round';
        ctx.beginPath();
        ctx.moveTo(xTop - stalkW * 0.68, yTop + 2);
        ctx.lineTo(xTop + stalkW * 0.68, yTop + 2);
        ctx.stroke();

        if ((n + stalk.seed) % 2 === 0 && n > 0 && n < stalk.nodes - 1) {
          const dir = (n + stalk.seed) % 4 === 0 ? 1 : -1;
          this._drawBambooLeafCluster(ctx, xTop, yTop + 2, dir, stalkW, ambientT, stalk.seed + n);
        }
      }
    });

    ctx.restore();
  }

  _drawBambooLeafCluster(ctx, x, y, dir, stalkW, ambientT, seed) {
    const breeze = Math.sin(ambientT * 2.0 + seed) * 0.08;
    const twigLen = 36 + (seed % 3) * 14;
    const endX = x + dir * twigLen;
    const endY = y - 16 + Math.sin(seed) * 10;

    ctx.save();
    ctx.strokeStyle = '#1E1D1A';
    ctx.fillStyle = '#1E1D1A';
    ctx.lineWidth = 1.4;

    ctx.beginPath();
    ctx.moveTo(x + dir * (stalkW * 0.4), y);
    ctx.quadraticCurveTo(x + dir * twigLen * 0.5, y - 12, endX, endY);
    ctx.stroke();

    const leafAngles = [0.25, 0.55, 0.85, 1.15];
    leafAngles.forEach((baseAng, idx) => {
      const len = 28 - idx * 3;
      const ang = (dir > 0 ? baseAng : Math.PI - baseAng) + breeze;
      ctx.save();
      ctx.translate(endX - dir * (idx * 5), endY + idx * 2);
      ctx.rotate(ang);
      ctx.beginPath();
      ctx.moveTo(0, 0);
      ctx.quadraticCurveTo(len * 0.45, -4.2, len, 0);
      ctx.quadraticCurveTo(len * 0.45, 4.2, 0, 0);
      ctx.closePath();
      ctx.fill();
      ctx.restore();
    });

    ctx.restore();
  }

  _drawInkSlopeAndTraveler(ctx, w, h, t, ambientT, weights) {
    const getGroundY = (normX) => {
      const hillArch = Math.sin(normX * Math.PI * 1.15 - 0.2) * (h * 0.055);
      const microRipple = Math.sin(normX * 9) * 2;
      return h * 0.87 - hillArch + microRipple;
    };

    ctx.save();
    ctx.globalAlpha = weights.sideTravelerAlpha;

    ctx.beginPath();
    ctx.moveTo(0, h);
    for (let i = 0; i <= 80; i++) {
      const nx = i / 80;
      ctx.lineTo(nx * w, getGroundY(nx));
    }
    ctx.lineTo(w, h);
    ctx.closePath();

    const groundGrad = ctx.createLinearGradient(0, h * 0.80, 0, h);
    groundGrad.addColorStop(0, '#787266');
    groundGrad.addColorStop(0.35, '#9E9688');
    groundGrad.addColorStop(1, '#D5CEC0');
    ctx.fillStyle = groundGrad;
    ctx.fill();

    ctx.beginPath();
    for (let i = 0; i <= 80; i++) {
      const nx = i / 80;
      const gx = nx * w;
      const gy = getGroundY(nx);
      if (i === 0) ctx.moveTo(gx, gy);
      else ctx.lineTo(gx, gy);
    }
    ctx.strokeStyle = '#22201D';
    ctx.lineWidth = 4.5;
    ctx.lineCap = 'round';
    ctx.stroke();

    ctx.strokeStyle = '#1C1B18';
    ctx.lineWidth = 1.6;
    this.inkGrass.forEach((g) => {
      const gx = g.x * w;
      const gy = getGroundY(g.x);
      const sway = 0;
      for (let b = 0; b < g.blades; b++) {
        const lean = (b - 1) * 5 + sway;
        ctx.beginPath();
        ctx.moveTo(gx, gy);
        ctx.quadraticCurveTo(gx + lean * 0.5, gy - g.height * 0.6, gx + lean, gy - g.height);
        ctx.stroke();
      }
    });

    // Traveler walks left-to-right (0.28 -> 0.54) and faces RIGHT (faceLeft = false)
    const walkProgress = this._smoothstep(0.0, 24.0, t);
    const travelerNormX = this._lerp(0.28, 0.54, walkProgress);
    const tx = travelerNormX * w;
    const ty = getGroundY(travelerNormX);

    this._drawSumieTraveler(ctx, tx, ty, ambientT, true, 0, false);

    ctx.restore();
  }

  /* --------------------------------------------------------------------------
   * PHASE B: NON-LOOPING 1ST-POV MOUNTAIN PASS TREK (23.5s – 33.5s)
   * Zero modulo repetition! 10 unique mountain ridge pairs advance continuously
   * from the horizon past the camera while the summit sanctuary & tree emerge ahead.
   * -------------------------------------------------------------------------- */
  _drawFirstPersonTrekScene(ctx, w, h, t, ambientT, povAlpha) {
    ctx.save();
    ctx.globalAlpha = povAlpha;

    // Continuous 0.0 -> 1.0 progression over the 10-second pass climb
    const trekProg = this._clamp((t - 23.5) / 10.0, 0, 1);

    // First-person walking head-bob and shoulder sway
    const stepPhase = ambientT * 4.5;
    const bobY = Math.abs(Math.sin(stepPhase)) * 8.5;
    const swayX = Math.cos(stepPhase * 0.5) * 9.5;
    const rollAngle = Math.sin(stepPhase * 0.5) * 0.008;

    ctx.translate(w * 0.5 + swayX, h * 0.5 + bobY);
    ctx.rotate(rollAngle);
    ctx.translate(-w * 0.5, -h * 0.5);

    // 1. Sky warming as we climb toward the sunrise pass
    const skyGrad = ctx.createLinearGradient(0, 0, 0, h * 0.68);
    skyGrad.addColorStop(0, this._lerpColor('#D7CFC0', '#C48A69', trekProg));
    skyGrad.addColorStop(0.55, this._lerpColor('#EAE3D5', '#ECA976', trekProg));
    skyGrad.addColorStop(1, this._lerpColor('#F5EFE4', '#FCE0B0', trekProg));
    ctx.fillStyle = skyGrad;
    ctx.fillRect(-40, -40, w + 80, h + 80);

    // Vanishing point rises slightly as we crest the summit ridge
    const vpX = w * 0.5 + Math.sin(trekProg * Math.PI) * (w * 0.03);
    const vpY = this._lerp(h * 0.48, h * 0.42, trekProg);

    // Radiant Sun Orb rising ahead at the top of the pass
    const sunRadius = this._lerp(Math.min(w, h) * 0.08, Math.min(w, h) * 0.16, trekProg);
    const passGlow = ctx.createRadialGradient(vpX, vpY - h * 0.06, 8, vpX, vpY, Math.max(w, h) * 0.5);
    passGlow.addColorStop(0, `rgba(255, 248, 224, ${0.7 + trekProg * 0.25})`);
    passGlow.addColorStop(0.35, `rgba(248, 195, 118, ${0.35 + trekProg * 0.35})`);
    passGlow.addColorStop(1, 'rgba(242, 236, 225, 0)');
    ctx.fillStyle = passGlow;
    ctx.fillRect(-40, -40, w + 80, h + 80);

    ctx.beginPath();
    ctx.arc(vpX, vpY - h * 0.05, sunRadius, 0, Math.PI * 2);
    ctx.fillStyle = `rgba(255, 250, 234, ${0.65 + trekProg * 0.35})`;
    ctx.fill();

    // 2. Distant Horizon Himalayan Spire & Emerging Summit Blossom Tree Silhouette Ahead
    ctx.beginPath();
    ctx.moveTo(vpX - w * 0.26, vpY + h * 0.04);
    ctx.quadraticCurveTo(vpX - w * 0.08, vpY - h * 0.16, vpX - w * 0.02, vpY - h * 0.27);
    ctx.quadraticCurveTo(vpX + w * 0.06, vpY - h * 0.14, vpX + w * 0.24, vpY + h * 0.04);
    ctx.closePath();
    const farPeakGrad = ctx.createLinearGradient(0, vpY - h * 0.27, 0, vpY + h * 0.04);
    farPeakGrad.addColorStop(0, '#6E665F');
    farPeakGrad.addColorStop(1, 'rgba(245, 222, 190, 0.15)');
    ctx.fillStyle = farPeakGrad;
    ctx.fill();

    // 3. NON-LOOPING Flanking Mountain Ridges (Each unique ridge moves from horizon -> past camera once)
    // Total camera travel in Z space = 1.15 units over the 10 seconds
    const cameraZ = trekProg * 1.15;

    // Sort back-to-front (largest relativeZ first)
    const activePairs = [];
    this.povMountainPairs.forEach((pair) => {
      // relZ: how far ahead of the camera this mountain pair is
      const relZ = pair.initialZ - cameraZ;
      // Visible when relZ is between 0.04 (right beside camera) and 1.05 (far horizon)
      if (relZ > 0.03 && relZ < 1.05) {
        activePairs.push({ pair, relZ });
      }
    });

    activePairs.sort((a, b) => b.relZ - a.relZ);

    activePairs.forEach(({ pair, relZ }) => {
      // closeness = 0 at far horizon, 1 right beside camera
      const closeness = 1.0 - this._clamp(relZ / 1.0, 0, 1);
      const persp = Math.pow(closeness, 1.45);

      const spreadX = this._lerp(w * 0.05, w * 0.58, persp);
      const baseWallY = this._lerp(vpY + h * 0.015, h * 0.92, persp);

      const lPeakH = this._lerp(h * 0.08, h * (0.35 + pair.leftHeight * 0.65), persp);
      const rPeakH = this._lerp(h * 0.08, h * (0.35 + pair.rightHeight * 0.65), persp);

      // Smooth fade-in at horizon and fade-out as it passes behind peripheral vision
      const edgeFade = this._smoothstep(0.0, 0.12, closeness) * (1.0 - this._smoothstep(0.88, 1.0, closeness));

      const wallColor = this._lerpColor('#B5AA99', '#38332E', closeness * 0.85);
      const outlineColor = this._lerpColor('#787065', '#1C1A17', closeness);

      ctx.save();
      ctx.globalAlpha = povAlpha * edgeFade;

      // --- Left Unique Mountain Ridge ---
      const lxPeak = vpX - spreadX - w * (0.09 + pair.leftSpreadOffset);
      const lyPeak = baseWallY - lPeakH;
      ctx.beginPath();
      ctx.moveTo(-60, h + 40);
      ctx.lineTo(-60, lyPeak + h * 0.10);
      if (pair.leftTwinPeak) {
        // Double-summit Himalayan massif shape
        ctx.quadraticCurveTo(lxPeak - w * 0.06, lyPeak - h * 0.03, lxPeak - w * 0.02, lyPeak + h * 0.03);
        ctx.quadraticCurveTo(lxPeak + w * 0.03, lyPeak - h * 0.02, vpX - spreadX * 0.30, baseWallY);
      } else {
        ctx.quadraticCurveTo(lxPeak, lyPeak, vpX - spreadX * 0.30, baseWallY);
      }
      ctx.lineTo(-60, h + 40);
      ctx.closePath();

      const lGrad = ctx.createLinearGradient(0, lyPeak, 0, baseWallY);
      lGrad.addColorStop(0, wallColor);
      lGrad.addColorStop(1, '#F2E6D4');
      ctx.fillStyle = lGrad;
      ctx.fill();

      ctx.strokeStyle = outlineColor;
      ctx.lineWidth = 2.0 + persp * 3.5;
      ctx.stroke();

      // --- Right Unique Mountain Ridge ---
      const rxPeak = vpX + spreadX + w * (0.09 + pair.rightSpreadOffset);
      const ryPeak = baseWallY - rPeakH;
      ctx.beginPath();
      ctx.moveTo(w + 60, h + 40);
      ctx.lineTo(w + 60, ryPeak + h * 0.10);
      if (pair.rightTwinPeak) {
        ctx.quadraticCurveTo(rxPeak + w * 0.05, ryPeak - h * 0.03, rxPeak + w * 0.01, ryPeak + h * 0.025);
        ctx.quadraticCurveTo(rxPeak - w * 0.03, ryPeak - h * 0.015, vpX + spreadX * 0.30, baseWallY);
      } else {
        ctx.quadraticCurveTo(rxPeak, ryPeak, vpX + spreadX * 0.30, baseWallY);
      }
      ctx.lineTo(w + 60, h + 40);
      ctx.closePath();

      const rGrad = ctx.createLinearGradient(0, ryPeak, 0, baseWallY);
      rGrad.addColorStop(0, wallColor);
      rGrad.addColorStop(1, '#F2E6D4');
      ctx.fillStyle = rGrad;
      ctx.fill();

      ctx.strokeStyle = outlineColor;
      ctx.stroke();

      ctx.restore();
    });

    // 4. Emerging Summit Blossom Tree Silhouette on the Right Horizon (Grows as trekProg -> 1)
    const treeReveal = this._smoothstep(0.35, 0.95, trekProg);
    if (treeReveal > 0.01) {
      ctx.save();
      ctx.globalAlpha = povAlpha * treeReveal * 0.85;
      const previewScale = this._lerp(0.18, 0.55, treeReveal);
      const previewX = this._lerp(vpX + w * 0.06, w * 0.72, treeReveal);
      const previewY = this._lerp(vpY + h * 0.02, h * 0.68, treeReveal);
      ctx.translate(previewX, previewY);
      ctx.scale(previewScale, previewScale);
      this._drawSummitTree(ctx, 0, 0, w, h, ambientT);
      ctx.restore();
    }

    // 5. First-Person Winding Trekking Trail Perspective
    const pathSteps = 45;
    const leftTrail = [];
    const rightTrail = [];

    ctx.fillStyle = '#8F8779';
    ctx.fillRect(-40, vpY, w + 80, h - vpY + 80);

    for (let i = 0; i <= pathSteps; i++) {
      const u = i / pathSteps;
      const perspY = vpY + Math.pow(u, 1.55) * (h - vpY + 30);
      const curveX = Math.sin(u * 3.2 - trekProg * 5.0) * (w * 0.08 * (1 - u * 0.35));
      const centerX = vpX + curveX;
      const halfWidth = this._lerp(w * 0.008, w * 0.34, Math.pow(u, 1.15));

      leftTrail.push({ x: centerX - halfWidth, y: perspY, u, centerX, halfWidth });
      rightTrail.push({ x: centerX + halfWidth, y: perspY, u });
    }

    ctx.beginPath();
    leftTrail.forEach((p, idx) => (idx === 0 ? ctx.moveTo(p.x, p.y) : ctx.lineTo(p.x, p.y)));
    for (let i = rightTrail.length - 1; i >= 0; i--) {
      ctx.lineTo(rightTrail[i].x, rightTrail[i].y);
    }
    ctx.closePath();

    const trailGrad = ctx.createLinearGradient(0, vpY, 0, h);
    trailGrad.addColorStop(0, '#E5D3B8');
    trailGrad.addColorStop(0.5, '#C2B49E');
    trailGrad.addColorStop(1, '#968B79');
    ctx.fillStyle = trailGrad;
    ctx.fill();

    ctx.strokeStyle = '#22201D';
    ctx.lineCap = 'round';
    ctx.lineWidth = 4.2;
    ctx.beginPath();
    leftTrail.forEach((p, idx) => (idx === 0 ? ctx.moveTo(p.x, p.y) : ctx.lineTo(p.x, p.y)));
    ctx.stroke();

    ctx.beginPath();
    rightTrail.forEach((p, idx) => (idx === 0 ? ctx.moveTo(p.x, p.y) : ctx.lineTo(p.x, p.y)));
    ctx.stroke();

    // Stone steps & trailside grass advancing toward feet
    const numRungs = 14;
    const rungScroll = (trekProg * 2.8) % (1 / numRungs);

    for (let r = 0; r < numRungs; r++) {
      const u = r / numRungs + rungScroll;
      if (u <= 0.06 || u >= 0.98) continue;

      const perspY = vpY + Math.pow(u, 1.55) * (h - vpY + 30);
      const curveX = Math.sin(u * 3.2 - trekProg * 5.0) * (w * 0.08 * (1 - u * 0.35));
      const centerX = vpX + curveX;
      const halfW = this._lerp(w * 0.008, w * 0.34, Math.pow(u, 1.15));

      ctx.strokeStyle = `rgba(34, 32, 29, ${u * 0.55})`;
      ctx.lineWidth = 1.2 + u * 3.8;
      ctx.beginPath();
      ctx.moveTo(centerX - halfW * 0.78, perspY);
      ctx.quadraticCurveTo(centerX, perspY + 4 * u, centerX + halfW * 0.78, perspY);
      ctx.stroke();
    }

    ctx.restore();
  }

  /* --------------------------------------------------------------------------
   * PHASE C: SCENE 5 — GRAND FINALE SUMMIT SANCTUARY & SUNRISE/SUNSET (33.5s – 48s+)
   * -------------------------------------------------------------------------- */
  _drawSummitSanctuaryMasterpiece(ctx, w, h, t, ambientT, weights) {
    const { summitWeight, sunriseGlory } = weights;

    ctx.save();
    ctx.globalAlpha = summitWeight;

    // 1. Sunrise / Sunset Sky Gradient
    const skyGrad = ctx.createLinearGradient(0, 0, 0, h * 0.78);
    skyGrad.addColorStop(0, this._lerpColor('#C9B093', '#B87B5C', sunriseGlory));
    skyGrad.addColorStop(0.32, this._lerpColor('#E2C8A8', '#DF9B6D', sunriseGlory));
    skyGrad.addColorStop(0.65, this._lerpColor('#F2DEC1', '#F7C286', sunriseGlory));
    skyGrad.addColorStop(1, '#FCE6BE');
    ctx.fillStyle = skyGrad;
    ctx.fillRect(0, 0, w, h);

    this._drawPaperFibers(ctx, w, h);

    // 2. Monumental Rising/Setting Sun Orb & Multi-Layered Golden Halo
    const sunX = w * 0.42;
    const sunY = this._lerp(h * 0.46, h * 0.36, sunriseGlory);
    const sunRadius = Math.min(w, h) * 0.175;

    const outerHalo = ctx.createRadialGradient(sunX, sunY, sunRadius * 0.3, sunX, sunY, Math.max(w, h) * 0.65);
    outerHalo.addColorStop(0, 'rgba(255, 250, 232, 0.92)');
    outerHalo.addColorStop(0.24, 'rgba(255, 212, 138, 0.65)');
    outerHalo.addColorStop(0.55, 'rgba(224, 128, 78, 0.28)');
    outerHalo.addColorStop(1, 'rgba(242, 236, 225, 0)');
    ctx.fillStyle = outerHalo;
    ctx.fillRect(0, 0, w, h);

    ctx.beginPath();
    ctx.arc(sunX, sunY, sunRadius, 0, Math.PI * 2);
    const discGrad = ctx.createLinearGradient(0, sunY - sunRadius, 0, sunY + sunRadius);
    discGrad.addColorStop(0, '#FFFDF5');
    discGrad.addColorStop(0.65, '#FFF0CC');
    discGrad.addColorStop(1, '#FAD493');
    ctx.fillStyle = discGrad;
    ctx.fill();

    // 3. Panoramic Himalayan Range across the Horizon
    const summitPeaks = [
      { x: 0.06, w: 0.13, h: 0.36 },
      { x: 0.22, w: 0.11, h: 0.56 },
      { x: 0.38, w: 0.12, h: 0.44 },
      { x: 0.54, w: 0.11, h: 0.52 },
      { x: 0.71, w: 0.14, h: 0.38 }
    ];

    this._renderInkMountainRange(ctx, w, h, {
      peaks: summitPeaks,
      baseY: h * 0.72,
      heightScale: 0.95,
      scrollOffset: 0,
      inkTopColor: '#6D615B',
      inkOutlineColor: '#423833',
      paperFadeColor: '#F9D6A4',
      alpha: 0.92
    });

    const midSummitPeaks = [
      { x: 0.14, w: 0.14, h: 0.28 },
      { x: 0.31, w: 0.13, h: 0.33 },
      { x: 0.48, w: 0.14, h: 0.29 },
      { x: 0.65, w: 0.15, h: 0.25 }
    ];
    this._renderInkMountainRange(ctx, w, h, {
      peaks: midSummitPeaks,
      baseY: h * 0.76,
      heightScale: 0.9,
      scrollOffset: 0,
      inkTopColor: '#544842',
      inkOutlineColor: '#2E2622',
      paperFadeColor: '#FCE2B6',
      alpha: 0.95
    });

    // 4. Drifting Golden Sea of Clouds
    this.summitCloudRibbons.forEach((c) => {
      const cx = (((c.x + ambientT * c.speed) % 1.4) + 1.4) % 1.4 - 0.2;
      const px = cx * w;
      const py = c.y * h;
      const rw = c.w * w;
      const rh = c.h * h;

      const cGrad = ctx.createRadialGradient(px, py, rh * 0.1, px, py, rw * 0.5);
      cGrad.addColorStop(0, `rgba(255, 245, 224, ${c.alpha})`);
      cGrad.addColorStop(0.6, `rgba(248, 214, 168, ${c.alpha * 0.5})`);
      cGrad.addColorStop(1, 'rgba(248, 214, 168, 0)');
      ctx.fillStyle = cGrad;
      ctx.beginPath();
      ctx.ellipse(px, py, rw * 0.5, rh, 0, 0, Math.PI * 2);
      ctx.fill();
    });

    // 5. Soaring Birds
    ctx.strokeStyle = 'rgba(42, 34, 28, 0.55)';
    ctx.lineWidth = 1.5;
    this.summitBirds.forEach((b, idx) => {
      const bx = (((b.x + ambientT * b.speedX) % 1.15) + 1.15) % 1.15 * w;
      const by = (b.y + Math.sin(ambientT * 0.6 + idx) * 0.012) * h;
      const wing = Math.sin(ambientT * 4.8 + b.phase) * 4.5;
      ctx.beginPath();
      ctx.moveTo(bx - 6, by + wing);
      ctx.quadraticCurveTo(bx - 2, by - 2, bx, by);
      ctx.quadraticCurveTo(bx + 2, by - 2, bx + 6, by + wing);
      ctx.stroke();
    });

    // 6. High Mountain Summit Cliff Promontory
    const getSummitCliffY = (nx) => {
      if (nx < 0.20) return h + 40;
      const plateau = this._smoothstep(0.20, 0.64, nx);
      const arch = Math.sin((nx - 0.55) * Math.PI * 1.1) * (h * 0.018);
      return this._lerp(h * 1.03, h * 0.77, plateau) - arch;
    };

    ctx.beginPath();
    ctx.moveTo(w * 0.18, h + 20);
    for (let i = 18; i <= 100; i++) {
      const nx = i / 100;
      ctx.lineTo(nx * w, getSummitCliffY(nx));
    }
    ctx.lineTo(w, h + 20);
    ctx.closePath();

    const cliffGrad = ctx.createLinearGradient(0, h * 0.74, 0, h);
    cliffGrad.addColorStop(0, '#3D3731');
    cliffGrad.addColorStop(0.45, '#595149');
    cliffGrad.addColorStop(1, '#26231F');
    ctx.fillStyle = cliffGrad;
    ctx.fill();

    ctx.beginPath();
    for (let i = 20; i <= 100; i++) {
      const nx = i / 100;
      const cx = nx * w;
      const cy = getSummitCliffY(nx);
      if (i === 20) ctx.moveTo(cx, cy);
      else ctx.lineTo(cx, cy);
    }
    ctx.strokeStyle = '#181614';
    ctx.lineWidth = 5.5;
    ctx.lineCap = 'round';
    ctx.stroke();

    ctx.strokeStyle = 'rgba(255, 218, 148, 0.55)';
    ctx.lineWidth = 2.0;
    ctx.stroke();

    // Calligraphic grass tufts on the summit ledge
    ctx.strokeStyle = '#181614';
    ctx.lineWidth = 1.6;
    for (let g = 0; g < 14; g++) {
      const gxNorm = 0.50 + (g / 14) * 0.45;
      const gx = gxNorm * w;
      const gy = getSummitCliffY(gxNorm);
      const sway = 0;
      ctx.beginPath();
      ctx.moveTo(gx, gy);
      ctx.quadraticCurveTo(gx - 3, gy - 10, gx - 6, gy - 16);
      ctx.moveTo(gx, gy);
      ctx.quadraticCurveTo(gx + 3, gy - 9, gx + 7, gy - 14);
      ctx.stroke();
    }

    // 7. Monumental Blossoming Tree on the Summit Promontory
    const treeBaseX = w * 0.85;
    const treeBaseY = getSummitCliffY(0.85) + 6;
    this._drawSummitTree(ctx, treeBaseX, treeBaseY, w, h, ambientT);

    // 8. Traveler Arriving from the Right Ridge (0.78 -> 0.67, moving LEFT while facing LEFT)
    // This guarantees the character walks forward naturally toward the viewpoint and stops beside the tree!
    const arrivalWalk = this._smoothstep(33.5, 39.0, t);
    const travNormX = this._lerp(0.78, 0.67, arrivalWalk);
    const travX = travNormX * w;
    const travY = getSummitCliffY(travNormX) + 2;
    const isStillWalking = t < 38.8;

    this._drawSumieTraveler(ctx, travX, travY, ambientT, isStillWalking, 1.0, true);

    ctx.restore();
  }

  _drawSummitTree(ctx, baseX, baseY, w, h, ambientT) {
    const scale = Math.min(w, h) * 0.96;
    const sway = Math.sin(ambientT * 1.05) * 0.0055;

    ctx.save();

    this.summitTree.segments.forEach((seg, idx) => {
      const x1 = baseX + seg.x1 * scale;
      const y1 = baseY + seg.y1 * scale;
      const cx = baseX + (seg.cx + sway * (idx * 0.4)) * scale;
      const cy = baseY + seg.cy * scale;
      const x2 = baseX + (seg.x2 + sway * (idx * 0.6 + 0.5)) * scale;
      const y2 = baseY + seg.y2 * scale;

      ctx.strokeStyle = 'rgba(28, 25, 22, 0.38)';
      ctx.lineWidth = seg.w1 * (scale / 780) + 6;
      ctx.lineCap = 'round';
      ctx.beginPath();
      ctx.moveTo(x1, y1);
      ctx.quadraticCurveTo(cx, cy, x2, y2);
      ctx.stroke();

      ctx.strokeStyle = '#161412';
      ctx.lineWidth = seg.w1 * (scale / 780);
      ctx.beginPath();
      ctx.moveTo(x1, y1);
      ctx.quadraticCurveTo(cx, cy, x2, y2);
      ctx.stroke();

      if (seg.w1 >= 10) {
        ctx.strokeStyle = 'rgba(248, 204, 136, 0.42)';
        ctx.lineWidth = Math.max(1.5, seg.w1 * 0.16 * (scale / 780));
        ctx.beginPath();
        ctx.moveTo(x1 - 3, y1 + 2);
        ctx.quadraticCurveTo(cx - 3, cy + 2, x2 - 2, y2 + 1);
        ctx.stroke();
      }
    });

    this.summitTree.blossoms.forEach((b) => {
      const bx = baseX + (b.x + sway * 2.5) * scale;
      const by = baseY + b.y * scale + Math.sin(ambientT * 1.4 + b.phase) * 2.5;
      const r = b.r * (scale / 820);
      this._drawFivePetalBlossom(ctx, bx, by, r, true);
    });

    ctx.restore();
  }

  _drawFivePetalBlossom(ctx, x, y, radius, warmTint = false) {
    ctx.save();
    ctx.translate(x, y);

    ctx.fillStyle = warmTint ? '#FFF7E8' : '#FAF6EC';
    ctx.strokeStyle = '#2B2824';
    ctx.lineWidth = 1.1;

    for (let p = 0; p < 5; p++) {
      const ang = (p * Math.PI * 2) / 5;
      const px = Math.cos(ang) * (radius * 0.55);
      const py = Math.sin(ang) * (radius * 0.55);
      ctx.beginPath();
      ctx.arc(px, py, radius * 0.48, 0, Math.PI * 2);
      ctx.fill();
      ctx.stroke();
    }

    ctx.fillStyle = warmTint ? '#D97B38' : '#2B2824';
    ctx.beginPath();
    ctx.arc(0, 0, radius * 0.18, 0, Math.PI * 2);
    ctx.fill();

    ctx.restore();
  }

  /* --------------------------------------------------------------------------
   * CORRECTED SUMI-E TRAVELER SILHOUETTE (CLEAR FORWARD WALKING POSTURE)
   * - Local +X is ALWAYS the forward direction of travel.
   * - Head & torso lean slightly forward (+X).
   * - Front arm extends forward (+X) holding the walking staff AHEAD of the body.
   * - Alternating feet step beneath the hem, and crimson scarf trails behind (-X).
   * -------------------------------------------------------------------------- */
  _drawSumieTraveler(ctx, x, y, ambientT, isWalking, sunriseRim = 0, faceLeft = false) {
    const scale = Math.min(this.width, this.height) / 800;
    const walkCycle = ambientT * 4.8;
    const stride = isWalking ? Math.sin(walkCycle) : 0;
    const bob = isWalking ? Math.abs(Math.cos(walkCycle)) * 2.4 : 0;
    const forwardLean = isWalking ? 3.5 : 1.0;

    ctx.save();
    ctx.translate(x, y);
    // If faceLeft is true, flip horizontally so +X points left (matching leftward walk)
    ctx.scale(faceLeft ? -scale : scale, scale);

    // 1. Detailed Hiking Boots & Leg Strides
    ctx.lineWidth = 3.6;
    ctx.lineCap = 'round';
    ctx.lineJoin = 'round';

    // Leg A (Front/Back alternating)
    const legAX = stride * 11;
    ctx.strokeStyle = '#2B2925';
    ctx.beginPath();
    ctx.moveTo(1 + forwardLean * 0.4, -20 - bob);
    ctx.lineTo(legAX * 0.5, -10 - bob * 0.5);
    ctx.lineTo(legAX, -2);
    ctx.stroke();

    // Boot A (Chunky trail sole & toe box)
    ctx.fillStyle = '#171614';
    ctx.beginPath();
    ctx.moveTo(legAX - 4, -2);
    ctx.lineTo(legAX + 7, -2);
    ctx.lineTo(legAX + 6, -5);
    ctx.lineTo(legAX - 3, -6);
    ctx.closePath();
    ctx.fill();

    // Leg B
    const legBX = -stride * 11;
    ctx.strokeStyle = '#3D3A34';
    ctx.beginPath();
    ctx.moveTo(-2 + forwardLean * 0.4, -20 - bob);
    ctx.lineTo(legBX * 0.5, -10 - bob * 0.5);
    ctx.lineTo(legBX, -2);
    ctx.stroke();

    // Boot B
    ctx.fillStyle = '#1E1D1A';
    ctx.beginPath();
    ctx.moveTo(legBX - 4, -2);
    ctx.lineTo(legBX + 7, -2);
    ctx.lineTo(legBX + 6, -5);
    ctx.lineTo(legBX - 3, -6);
    ctx.closePath();
    ctx.fill();

    // 2. Trailing Inner Layer / Cloak Shadow (-X)
    ctx.fillStyle = '#5A564E';
    ctx.beginPath();
    ctx.moveTo(-4 + forwardLean, -52 - bob);
    ctx.quadraticCurveTo(-18 - Math.abs(stride) * 3, -28 - bob, -15 - stride * 4, -5);
    ctx.lineTo(-2, -5);
    ctx.closePath();
    ctx.fill();

    // 3. Expedition Backpack on the Traveler's Back (-X)
    ctx.fillStyle = '#33312B';
    ctx.beginPath();
    // Backpack body contour
    ctx.moveTo(-5 + forwardLean, -64 - bob);
    ctx.quadraticCurveTo(-18 + forwardLean, -58 - bob, -17 + forwardLean, -42 - bob);
    ctx.quadraticCurveTo(-16 + forwardLean, -32 - bob, -7 + forwardLean, -35 - bob);
    ctx.lineTo(-5 + forwardLean, -50 - bob);
    ctx.closePath();
    ctx.fill();

    // Bedroll / Sleeping pad strapped on top of pack
    ctx.strokeStyle = '#5E594F';
    ctx.lineWidth = 3.5;
    ctx.beginPath();
    ctx.moveTo(-16 + forwardLean, -65 - bob);
    ctx.lineTo(-6 + forwardLean, -67 - bob);
    ctx.stroke();

    // Backpack cinch compression straps (Subtle vermilion/amber accent lines)
    ctx.strokeStyle = '#C8442F';
    ctx.lineWidth = 1.2;
    ctx.beginPath();
    ctx.moveTo(-17 + forwardLean, -52 - bob);
    ctx.lineTo(-7 + forwardLean, -50 - bob);
    ctx.moveTo(-16 + forwardLean, -43 - bob);
    ctx.lineTo(-6 + forwardLean, -41 - bob);
    ctx.stroke();

    // 4. Main Expedition Jacket & Torso (Deep Sumi-e Charcoal)
    ctx.fillStyle = '#1A1916';
    ctx.beginPath();
    ctx.moveTo(-5 + forwardLean, -67 - bob); // High collar back
    ctx.lineTo(6 + forwardLean, -65 - bob);  // High collar front
    ctx.quadraticCurveTo(13 + forwardLean, -42 - bob, 11 + stride * 2, -6); // Front jacket hem
    ctx.lineTo(-9 - stride * 2, -6); // Back hem
    ctx.quadraticCurveTo(-12, -38 - bob, -5 + forwardLean, -67 - bob);
    ctx.closePath();
    ctx.fill();

    // High Standing Storm Collar protecting the neck
    ctx.strokeStyle = '#2B2A27';
    ctx.lineWidth = 2.4;
    ctx.beginPath();
    ctx.moveTo(-4 + forwardLean, -68 - bob);
    ctx.lineTo(2 + forwardLean, -72 - bob);
    ctx.lineTo(6 + forwardLean, -66 - bob);
    ctx.stroke();

    // Front Chest Zipper / Storm Flap (Fine ink highlight)
    ctx.strokeStyle = 'rgba(242, 236, 225, 0.7)';
    ctx.lineWidth = 1.4;
    ctx.beginPath();
    ctx.moveTo(3 + forwardLean, -65 - bob);
    ctx.quadraticCurveTo(7 + forwardLean, -50 - bob, 8 + forwardLean, -32 - bob);
    ctx.stroke();

    // Backpack Shoulder Harness Strap across chest
    ctx.strokeStyle = '#423F38';
    ctx.lineWidth = 2.0;
    ctx.beginPath();
    ctx.moveTo(-2 + forwardLean, -66 - bob);
    ctx.lineTo(6 + forwardLean, -50 - bob);
    ctx.stroke();

    // 5. Forward Arm Reaching AHEAD (+X) Gripping the Trekking Staff
    const armSwing = isWalking ? stride * 3.5 : 0;
    const handX = 18 + forwardLean + armSwing * 0.6;
    const handY = -47 - bob - armSwing * 0.3;

    // Sleeve
    ctx.strokeStyle = '#1A1916';
    ctx.lineWidth = 6.2;
    ctx.lineCap = 'round';
    ctx.lineJoin = 'round';
    ctx.beginPath();
    ctx.moveTo(3 + forwardLean, -58 - bob);
    ctx.quadraticCurveTo(11 + forwardLean, -50 - bob, handX, handY);
    ctx.stroke();

    // Hand gripping the staff (visible knuckles / thumb)
    ctx.fillStyle = '#C8B9A6';
    ctx.beginPath();
    ctx.arc(handX, handY, 2.6, 0, Math.PI * 2);
    ctx.fill();

    // 6. Carved Trekking Staff (Held firmly ahead with strap and tip)
    ctx.strokeStyle = '#2A241E';
    ctx.lineWidth = 2.4;
    ctx.beginPath();
    // Top knob of staff above the hand
    ctx.moveTo(handX - 2, handY - 24);
    // Shaft through hand down to ground contact ahead
    ctx.lineTo(handX + 6 + armSwing * 0.5, -1);
    ctx.stroke();

    // Staff grip wrap & wrist strap
    ctx.strokeStyle = '#C8442F';
    ctx.lineWidth = 1.4;
    ctx.beginPath();
    ctx.moveTo(handX - 1.5, handY - 10);
    ctx.lineTo(handX + 0.5, handY + 6);
    ctx.stroke();

    // Staff snow basket ring near tip
    ctx.strokeStyle = '#3A3833';
    ctx.lineWidth = 1.8;
    ctx.beginPath();
    const basketX = handX + 5 + armSwing * 0.4;
    ctx.moveTo(basketX - 3, -6);
    ctx.lineTo(basketX + 3, -6);
    ctx.stroke();

    // 7. Head & Natural Wind-Ruffled Hair (NO HAT / NO TOPI)
    // Head shape & face profile looking forward (+X)
    ctx.fillStyle = '#2B2A27';
    ctx.beginPath();
    ctx.arc(3 + forwardLean, -73 - bob, 6.8, 0, Math.PI * 2);
    ctx.fill();

    // Natural expressive hair silhouette (wind sweeping back slightly, organic brush strokes)
    ctx.fillStyle = '#1A1916';
    ctx.beginPath();
    ctx.moveTo(-5 + forwardLean, -73 - bob); // Back nape
    ctx.quadraticCurveTo(-7 + forwardLean, -81 - bob, 1 + forwardLean, -82 - bob); // Crown
    ctx.quadraticCurveTo(8 + forwardLean, -82 - bob, 10 + forwardLean, -76 - bob); // Front hairline
    ctx.lineTo(9 + forwardLean, -73 - bob); // Forehead
    ctx.quadraticCurveTo(6 + forwardLean, -76 - bob, 1 + forwardLean, -77 - bob);
    ctx.closePath();
    ctx.fill();

    // Fine calligraphic wind-blown strands of hair behind the head
    ctx.strokeStyle = '#1A1916';
    ctx.lineWidth = 1.2;
    ctx.beginPath();
    ctx.moveTo(1 + forwardLean, -82 - bob);
    ctx.quadraticCurveTo(-4 + forwardLean, -85 - bob, -8 + forwardLean, -82 - bob);
    ctx.moveTo(-2 + forwardLean, -80 - bob);
    ctx.quadraticCurveTo(-7 + forwardLean, -82 - bob, -11 + forwardLean, -78 - bob);
    ctx.stroke();

    // Focused facial profile (brow, nose tip looking toward the peaks)
    ctx.strokeStyle = '#1A1916';
    ctx.lineWidth = 1.6;
    ctx.beginPath();
    ctx.moveTo(9 + forwardLean, -75 - bob); // Brow
    ctx.lineTo(11 + forwardLean, -73 - bob); // Nose
    ctx.lineTo(8.5 + forwardLean, -70 - bob); // Lips/chin
    ctx.stroke();

    // 8. Flowing Vermilion Scarf catching the Himalayan breeze
    const windWave1 = Math.sin(ambientT * 5.2) * 8;
    const windWave2 = Math.cos(ambientT * 4.5) * 11;
    ctx.strokeStyle = '#B8332A';
    ctx.lineWidth = 2.4;
    ctx.beginPath();
    ctx.moveTo(-2 + forwardLean, -64 - bob);
    ctx.bezierCurveTo(
      -18, -60 - bob + windWave1 * 0.5,
      -32, -50 - bob + windWave1,
      -46, -42 - bob + windWave2
    );
    ctx.stroke();

    ctx.lineWidth = 1.4;
    ctx.beginPath();
    ctx.moveTo(-2 + forwardLean, -62 - bob);
    ctx.bezierCurveTo(
      -14, -54 - bob - windWave1 * 0.4,
      -26, -46 - bob + windWave2 * 0.6,
      -38, -36 - bob - windWave1
    );
    ctx.stroke();

    // 9. Golden Sunrise Rim-Light at the Summit (Hair, shoulder, backpack & staff glow)
    if (sunriseRim > 0.1) {
      ctx.strokeStyle = `rgba(232, 162, 91, ${0.9 * sunriseRim})`;
      ctx.lineWidth = 1.8;
      ctx.beginPath();
      // Glow on crown of hair
      ctx.moveTo(-6 + forwardLean, -81 - bob);
      ctx.lineTo(1 + forwardLean, -83 - bob);
      ctx.lineTo(9 + forwardLean, -76 - bob);
      // Glow on backpack shoulder
      ctx.moveTo(-5 + forwardLean, -65 - bob);
      ctx.lineTo(-14 + forwardLean, -60 - bob);
      // Glow on staff
      ctx.moveTo(handX - 2, handY - 24);
      ctx.lineTo(handX - 1, handY - 10);
      ctx.stroke();
    }

    ctx.restore();
  }

  /* --------------------------------------------------------------------------
   * FLOATING BLOSSOM PETALS & INK LEAVES + VIGNETTE
   * -------------------------------------------------------------------------- */
  _drawFloatingInkParticles(ctx, w, h, ambientT, weights) {
    ctx.save();

    this.floatingParticles.forEach((p, idx) => {
      const px = (((p.x + ambientT * p.speedX) % 1.1) + 1.1) % 1.1 * w;
      const py = (((p.y + ambientT * p.speedY) % 1.05) + 1.05) % 1.05 * h;
      const swayX = Math.sin(ambientT * 1.8 + idx) * 14;
      const rot = p.angle + ambientT * p.spin;

      ctx.save();
      ctx.translate(px + swayX, py);
      ctx.rotate(rot);

      const useBambooLeaf = (p.type === 'bambooLeaf' && weights.summitWeight < 0.5) || weights.bambooPresence > 0.3;

      if (useBambooLeaf) {
        ctx.fillStyle = '#23211E';
        ctx.globalAlpha = 0.18 + p.depth * 0.42;
        const len = p.size * 2.4;
        ctx.beginPath();
        ctx.moveTo(-len * 0.5, 0);
        ctx.quadraticCurveTo(0, -p.size * 0.4, len * 0.5, 0);
        ctx.quadraticCurveTo(0, p.size * 0.4, -len * 0.5, 0);
        ctx.closePath();
        ctx.fill();
      } else {
        ctx.globalAlpha = 0.5 + p.depth * 0.45;
        ctx.fillStyle = weights.summitWeight > 0.5 ? '#FFF5E4' : '#FAF6EC';
        ctx.strokeStyle = '#3A3630';
        ctx.lineWidth = 0.9;
        ctx.beginPath();
        ctx.ellipse(0, 0, p.size * 0.85, p.size * 0.5, 0, 0, Math.PI * 2);
        ctx.fill();
        ctx.stroke();
      }

      ctx.restore();
    });

    ctx.restore();
  }

  _drawScrollVignette(ctx, w, h, t) {
    const vig = ctx.createRadialGradient(
      w * 0.5, h * 0.5, Math.min(w, h) * 0.36,
      w * 0.5, h * 0.5, Math.max(w, h) * 0.76
    );
    vig.addColorStop(0, 'rgba(230, 222, 208, 0)');
    vig.addColorStop(1, 'rgba(148, 132, 114, 0.34)');
    ctx.fillStyle = vig;
    ctx.fillRect(0, 0, w, h);

    const openFade = 1.0 - this._smoothstep(0.0, 2.2, t);
    if (openFade > 0.01) {
      ctx.fillStyle = `rgba(242, 236, 225, ${openFade * 0.85})`;
      ctx.fillRect(0, 0, w, h);
    }
  }

  /* --- ANIMATION LOOP & PORTABLE API --- */
  _tick(now) {
    if (!this.isPlaying) return;
    if (!this.lastFrameTime) this.lastFrameTime = now;

    const dt = Math.min((now - this.lastFrameTime) / 1000, 0.1);
    this.lastFrameTime = now;

    this.ambientTime += dt;

    if (this.elapsed < this.config.duration) {
      this.elapsed = Math.min(this.elapsed + dt, this.config.duration);
      this._notifyListeners();

      if (this.elapsed >= this.config.duration && !this.hasCompleted) {
        this.hasCompleted = true;
        if (typeof this.config.onComplete === 'function') {
          this.config.onComplete();
        }
        if (!this.config.keepAliveAtEnd) {
          this.pause();
          return;
        }
      }
    }

    this.render(this.elapsed, this.ambientTime);
    this.rafId = requestAnimationFrame(this._boundTick);
  }

  _notifyListeners() {
    const activeScene = this.scenes.find(
      (s) => this.elapsed >= s.start && this.elapsed <= s.end
    ) || this.scenes[this.scenes.length - 1];

    if (activeScene && activeScene.index !== this.currentSceneIndex) {
      this.currentSceneIndex = activeScene.index;
      if (typeof this.config.onSceneChange === 'function') {
        this.config.onSceneChange(activeScene);
      }
    }

    if (typeof this.config.onTimeUpdate === 'function') {
      this.config.onTimeUpdate({
        elapsed: this.elapsed,
        duration: this.config.duration,
        progress: this.elapsed / this.config.duration,
        scene: activeScene
      });
    }
  }

  play() {
    if (this.isPlaying) return;
    if (this.elapsed >= this.config.duration && !this.config.keepAliveAtEnd) {
      this.elapsed = 0;
      this.ambientTime = 0;
      this.hasCompleted = false;
    }
    this.isPlaying = true;
    this.lastFrameTime = performance.now();
    this.rafId = requestAnimationFrame(this._boundTick);
  }

  pause() {
    this.isPlaying = false;
    this.lastFrameTime = 0;
    if (this.rafId) {
      cancelAnimationFrame(this.rafId);
      this.rafId = null;
    }
  }

  restart() {
    this.elapsed = 0;
    this.ambientTime = 0;
    this.hasCompleted = false;
    this.currentSceneIndex = -1;
    this.render(0, 0);
    this._notifyListeners();
    this.play();
  }

  seek(seconds) {
    this.elapsed = this._clamp(seconds, 0, this.config.duration);
    this.ambientTime = this.elapsed;
    this.hasCompleted = this.elapsed >= this.config.duration;
    this.currentSceneIndex = -1;
    this.render(this.elapsed, this.ambientTime);
    this._notifyListeners();
  }

  resize() {
    const rect = this.canvas.parentElement
      ? this.canvas.parentElement.getBoundingClientRect()
      : { width: window.innerWidth, height: window.innerHeight };

    this.width = Math.max(300, rect.width);
    this.height = Math.max(250, rect.height);
    this.dpr = Math.min(window.devicePixelRatio || 1, this.config.maxDPR);

    this.canvas.width = Math.round(this.width * this.dpr);
    this.canvas.height = Math.round(this.height * this.dpr);
    this.ctx.setTransform(this.dpr, 0, 0, this.dpr, 0, 0);

    this.render(this.elapsed, this.ambientTime);
  }

  destroy() {
    this.pause();
    window.removeEventListener('resize', this._boundResize);
  }
}

/* --- WEB AUDIO SYNTHESIZER (MOUNTAIN WIND & SINGING BOWL HARMONICS) --- */
class HimalayanSoundscape {
  constructor() {
    this.ctx = null;
    this.isMuted = true;
    this.masterGain = null;
    this.chimeInterval = null;
  }

  toggle() {
    if (!this.ctx) {
      this._initAudio();
    }
    this.isMuted = !this.isMuted;
    if (this.ctx.state === 'suspended') {
      this.ctx.resume();
    }
    const targetGain = this.isMuted ? 0.0 : 0.22;
    this.masterGain.gain.setTargetAtTime(targetGain, this.ctx.currentTime, 0.4);
    return !this.isMuted;
  }

  _initAudio() {
    const AudioCtx = window.AudioContext || window.webkitAudioContext;
    this.ctx = new AudioCtx();
    this.masterGain = this.ctx.createGain();
    this.masterGain.gain.value = 0;
    this.masterGain.connect(this.ctx.destination);

    [174.61, 261.63, 349.23].forEach((freq, idx) => {
      const osc = this.ctx.createOscillator();
      const oscGain = this.ctx.createGain();
      osc.type = 'sine';
      osc.frequency.value = freq;
      oscGain.gain.value = 0.08 / (idx + 1);
      osc.connect(oscGain);
      oscGain.connect(this.masterGain);
      osc.start();
    });

    const notes = [523.25, 659.25, 783.99, 587.33];
    let step = 0;
    this.chimeInterval = setInterval(() => {
      if (this.isMuted || !this.ctx) return;
      const now = this.ctx.currentTime;
      const osc = this.ctx.createOscillator();
      const gain = this.ctx.createGain();
      osc.type = 'sine';
      osc.frequency.value = notes[step % notes.length];
      step++;

      gain.gain.setValueAtTime(0.001, now);
      gain.gain.exponentialRampToValueAtTime(0.12, now + 0.08);
      gain.gain.exponentialRampToValueAtTime(0.0001, now + 4.8);

      osc.connect(gain);
      gain.connect(this.masterGain);
      osc.start(now);
      osc.stop(now + 5.0);
    }, 6500);
  }
}

/* --- PRODUCTION INTEGRATION BOOTSTRAP (NON-LOOPING HERO VIDEO) --- */
document.addEventListener('DOMContentLoaded', () => {
  const canvas = document.getElementById('vibetour-canvas');
  if (!canvas) return;

  const brandFinale = document.getElementById('brand-finale');
  const btnPlayPause = document.getElementById('btn-play-pause');
  const iconPlayPause = document.getElementById('icon-play-pause');
  const btnRestart = document.getElementById('btn-restart');
  const btnAudio = document.getElementById('btn-audio');
  const iconAudio = document.getElementById('icon-audio');
  const btnFullscreen = document.getElementById('btn-fullscreen');
  const replayCta = document.getElementById('replay-cta');

  const progressFill = document.getElementById('hud-progress-fill');
  const progressWrap = document.getElementById('progress-bar-Click');
  const sceneIndicator = document.getElementById('hud-scene-indicator');
  const timeDisplay = document.getElementById('hud-time');

  const soundscape = new HimalayanSoundscape();

  const formatTime = (sec) => {
    const s = Math.floor(sec);
    const m = Math.floor(s / 60);
    const rem = s % 60;
    return `${String(m).padStart(2, '0')}:${String(rem).padStart(2, '0')}`;
  };

  const animation = new VibeTourAnimation(canvas, {
    duration: 48.0,
    keepAliveAtEnd: true,   // Keeps the peaceful summit scene alive; DOES NOT LOOP
    autoPlay: true,
    onSceneChange: (scene) => {
      if (sceneIndicator) sceneIndicator.textContent = scene.label;
    },
    onTimeUpdate: ({ elapsed, duration, progress }) => {
      if (progressFill) progressFill.style.width = `${(progress * 100).toFixed(2)}%`;
      if (timeDisplay) timeDisplay.textContent = `${formatTime(elapsed)} / ${formatTime(duration)}`;

      // Reveal the stationary VibeTrip branding once the traveler reaches the Summit (39.5s+)
      if (brandFinale) {
        if (elapsed >= 39.5) {
          brandFinale.classList.add('is-visible');
          brandFinale.setAttribute('aria-hidden', 'false');
          try { sessionStorage.setItem('vibetrip_intro_seen', 'true'); } catch (e) {}
        } else {
          brandFinale.classList.remove('is-visible');
          brandFinale.setAttribute('aria-hidden', 'true');
        }
      }
    }
  });

  // Skip Intro & Reduced Motion handling
  const prefersReducedMotion = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  let introAlreadySeen = false;
  try {
    introAlreadySeen = sessionStorage.getItem('vibetrip_intro_seen') === 'true';
  } catch (e) {}

  const urlParams = new URLSearchParams(window.location.search);
  const skipIntroParam = urlParams.has('skip_intro') || urlParams.has('no_intro');

  if (prefersReducedMotion || introAlreadySeen || skipIntroParam) {
    // Jump straight to peaceful stationary summit scene
    animation.seek(39.5);
    if (brandFinale) {
      brandFinale.classList.add('is-visible');
      brandFinale.setAttribute('aria-hidden', 'false');
    }
    if (skipIntroParam) {
      const stage = document.getElementById('vibetour-stage');
      if (stage) stage.style.display = 'none';
    }
  }

  // Skip Button Listener
  const btnSkipIntro = document.getElementById('btn-skip-intro');
  if (btnSkipIntro) {
    btnSkipIntro.addEventListener('click', (e) => {
      e.preventDefault();
      try { sessionStorage.setItem('vibetrip_intro_seen', 'true'); } catch (err) {}
      animation.seek(40.0);
      if (brandFinale) {
        brandFinale.classList.add('is-visible');
        brandFinale.setAttribute('aria-hidden', 'false');
      }
      const target = document.getElementById('home-main');
      if (target) {
        target.scrollIntoView({ behavior: 'smooth' });
      }
    });
  }

  const togglePlay = () => {
    if (animation.isPlaying) {
      animation.pause();
      if (iconPlayPause) iconPlayPause.textContent = 'Play';
    } else {
      animation.play();
      if (iconPlayPause) iconPlayPause.textContent = 'Pause';
    }
  };

  if (btnPlayPause) btnPlayPause.addEventListener('click', togglePlay);

  const handleRestart = () => {
    if (brandFinale) brandFinale.classList.remove('is-visible');
    animation.restart();
    if (iconPlayPause) iconPlayPause.textContent = 'Pause';
  };

  if (btnRestart) btnRestart.addEventListener('click', handleRestart);
  if (replayCta) replayCta.addEventListener('click', handleRestart);

  if (btnAudio) {
    btnAudio.addEventListener('click', () => {
      const active = soundscape.toggle();
      if (iconAudio) iconAudio.textContent = active ? 'Sound: On' : 'Sound: Off';
    });
  }

  if (btnFullscreen) {
    btnFullscreen.addEventListener('click', () => {
      const stage = document.getElementById('vibetour-stage');
      if (!stage) return;
      if (!document.fullscreenElement) {
        stage.requestFullscreen?.();
      } else {
        document.exitFullscreen?.();
      }
    });
  }

  if (progressWrap) {
    progressWrap.addEventListener('click', (e) => {
      const rect = progressWrap.getBoundingClientRect();
      const clickRatio = (e.clientX - rect.left) / rect.width;
      animation.seek(clickRatio * animation.config.duration);
    });
  }

  // URL parameters for visual verification and testing
  const seekT = urlParams.get('seek_t');
  if (seekT !== null) {
    animation.seek(parseFloat(seekT));
    if (urlParams.get('paused') === 'true') {
      animation.pause();
    }
  }
  const testScroll = urlParams.get('test_scroll');
  if (testScroll !== null) {
    window.scrollTo(0, parseInt(testScroll, 10));
  }

  // Smooth scroll handler for all explore/journal buttons
  document.querySelectorAll('a[href^="#home-main"]').forEach(link => {
    link.addEventListener('click', (e) => {
      const target = document.getElementById('home-main');
      if (target) {
        e.preventDefault();
        target.scrollIntoView({ behavior: 'smooth' });
      }
    });
  });

  // Top navigation bar reveals on scroll down past the hero
  const siteHeader = document.querySelector('.site-header');
  if (siteHeader) {
    document.body.classList.add('has-intro');
    const updateNavVisibility = () => {
      if (window.scrollY > 80) {
        siteHeader.classList.add('nav-revealed');
      } else {
        siteHeader.classList.remove('nav-revealed');
      }
    };
    window.addEventListener('scroll', updateNavVisibility, { passive: true });
    updateNavVisibility();
  }

  // Keyboard shortcuts (only when not typing in form inputs)
  window.addEventListener('keydown', (e) => {
    const tag = (e.target.tagName || '').toLowerCase();
    if (tag === 'input' || tag === 'textarea' || tag === 'select' || e.target.isContentEditable) return;

    if (e.code === 'Space') {
      e.preventDefault();
      togglePlay();
    } else if (e.key === 'r' || e.key === 'R') {
      handleRestart();
    } else if (e.key === 'm' || e.key === 'M') {
      if (btnAudio) btnAudio.click();
    } else if (e.key === 'f' || e.key === 'F') {
      if (btnFullscreen) btnFullscreen.click();
    }
  });
});

if (typeof window !== 'undefined') {
  window.VibeTourAnimation = VibeTourAnimation;
}