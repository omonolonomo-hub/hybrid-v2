/**
 * Canvas parcacik sistemi - v2/scenes/menu.py Particle ve FloatingShape
 * siniflarinin JS karsiligi.
 * 
 * Shared constants (CATEGORY_COLORS, DESIGN, hexToRgba) loaded from shared/canvas-utils.js
 */

const SCREEN = { W: window.innerWidth, H: window.innerHeight };
const INV_PHI = 0.61803398875;
const INV_PHI_SQ = 1 - INV_PHI;
const MAX_PARTICLES = 42;
const GOLDEN_Y_RATIOS = [0.118, 0.236, INV_PHI_SQ, 0.5, INV_PHI, 0.764, 0.882];
const CHAIN_LANES = [
  { y: GOLDEN_Y_RATIOS[0], direction: 1, angle: 0.026, alpha: 0.105, speed: 18, color: 0 },
  { y: GOLDEN_Y_RATIOS[1], direction: -1, angle: -0.030, alpha: 0.095, speed: 16, color: 4 },
  { y: GOLDEN_Y_RATIOS[2], direction: 1, angle: 0.020, alpha: 0.075, speed: 14, color: 1 },
  { y: GOLDEN_Y_RATIOS[3], direction: -1, angle: -0.018, alpha: 0.058, speed: 12, color: 3 },
  { y: GOLDEN_Y_RATIOS[4], direction: 1, angle: 0.022, alpha: 0.064, speed: 13, color: 2 },
];

const canvas = document.getElementById("bg-canvas");
const ctx = canvas.getContext("2d");

function resizeCanvas() {
  const dpr = 1;
  SCREEN.W = Math.max(window.innerWidth, 1);
  SCREEN.H = Math.max(window.innerHeight, 1);
  canvas.width = Math.round(SCREEN.W * dpr);
  canvas.height = Math.round(SCREEN.H * dpr);
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0);

  const scale = Math.min(SCREEN.W / DESIGN.W, SCREEN.H / DESIGN.H, 1);
  document.documentElement.style.setProperty("--ui-scale", scale.toFixed(4));
}

resizeCanvas();
window.addEventListener("resize", resizeCanvas);

class Particle {
  constructor() {
    this.reset();
  }

  reset() {
    this.x = Math.random() * SCREEN.W;
    this.y = SCREEN.H + 10;
    this.vx = (Math.random() - 0.5) * 40;
    this.vy = -(Math.random() * 40 + 40);
    this.color = CATEGORY_COLORS[Math.floor(Math.random() * CATEGORY_COLORS.length)];
    this.size = Math.random() * 2 + 1;
    this.alpha = (Math.random() * 90 + 30) / 255;
    this.life = Math.random() * 0.5 + 0.5;
  }

  update(dt) {
    this.x += this.vx * dt;
    this.y += this.vy * dt;
    this.life -= dt * 0.2;
    return this.life > 0;
  }

  draw() {
    const alpha = this.alpha * this.life;
    if (alpha < 0.02) return;

    for (let i = 0; i < 2; i += 1) {
      const radius = this.size * (1 + i * 0.5);
      ctx.beginPath();
      ctx.arc(this.x, this.y, radius, 0, Math.PI * 2);
      ctx.fillStyle = hexToRgba(this.color, alpha / (i + 1));
      ctx.fill();
    }
  }
}

class FloatingShape {
  constructor() {
    this.x = Math.random() * SCREEN.W;
    this.y = Math.random() * SCREEN.H;
    this.vx = (Math.random() - 0.5) * 30;
    this.vy = (Math.random() - 0.5) * 30;
    this.rotation = Math.random() * Math.PI * 2;
    this.rotationSpeed = (Math.random() - 0.5) * Math.PI / 3;
    this.size = Math.random() * 40 + 20;
    this.type = ["hex", "triangle", "square"][Math.floor(Math.random() * 3)];
    this.color = CATEGORY_COLORS[Math.floor(Math.random() * CATEGORY_COLORS.length)];
    this.alpha = (Math.random() * 25 + 15) / 255;
  }

  update(dt) {
    this.x += this.vx * dt;
    this.y += this.vy * dt;
    this.rotation += this.rotationSpeed * dt;

    if (this.x < -this.size || this.x > SCREEN.W + this.size) this.vx *= -1;
    if (this.y < -this.size || this.y > SCREEN.H + this.size) this.vy *= -1;
  }

  draw() {
    ctx.save();
    ctx.translate(this.x, this.y);
    ctx.rotate(this.rotation);
    ctx.strokeStyle = hexToRgba(this.color, this.alpha);
    ctx.lineWidth = 2;
    ctx.beginPath();

    if (this.type === "hex") {
      for (let i = 0; i < 6; i += 1) {
        const angle = (Math.PI / 3) * i;
        if (i === 0) {
          ctx.moveTo(Math.cos(angle) * this.size, Math.sin(angle) * this.size);
        } else {
          ctx.lineTo(Math.cos(angle) * this.size, Math.sin(angle) * this.size);
        }
      }
    } else if (this.type === "triangle") {
      for (let i = 0; i < 3; i += 1) {
        const angle = (Math.PI * 2 / 3) * i - Math.PI / 2;
        if (i === 0) {
          ctx.moveTo(Math.cos(angle) * this.size, Math.sin(angle) * this.size);
        } else {
          ctx.lineTo(Math.cos(angle) * this.size, Math.sin(angle) * this.size);
        }
      }
    } else {
      ctx.rect(-this.size / 2, -this.size / 2, this.size, this.size);
    }

    ctx.closePath();
    ctx.stroke();
    ctx.restore();
  }
}

class HexChain {
  constructor(index) {
    this.index = index;
    this.reset(true);
  }

  reset(initial = false) {
    this.lane = CHAIN_LANES[this.index % CHAIN_LANES.length];
    const colorIndex = this.lane.color;
    this.color = CATEGORY_COLORS[colorIndex];
    this.count = 5 + Math.floor(Math.random() * 3);
    this.spacing = 62 + Math.random() * 24;
    this.radius = 16 + Math.random() * 10;
    this.angle = this.lane.angle;
    this.direction = this.lane.direction;
    this.speed = this.lane.speed + Math.random() * 8;
    this.wave = 4 + Math.random() * 8;
    this.phase = Math.random() * Math.PI * 2;
    this.alpha = this.lane.alpha;
    this.driftX = Math.cos(this.angle) * this.speed * this.direction;
    this.driftY = Math.sin(this.angle) * this.speed * 0.35;
    const margin = this.count * this.spacing;
    this.x = initial
      ? Math.random() * SCREEN.W
      : this.direction > 0
        ? -margin
        : SCREEN.W + margin;
    this.y = SCREEN.H * this.lane.y + (Math.random() - 0.5) * 24;
  }

  update(dt) {
    this.phase += dt * 1.8;
    this.x += this.driftX * dt;
    this.y += this.driftY * dt;

    const margin = this.count * this.spacing + 120;
    const passedHorizontalEdge = this.direction > 0
      ? this.x > SCREEN.W + margin
      : this.x < -margin;
    if (passedHorizontalEdge || this.y < -margin || this.y > SCREEN.H + margin) {
      this.reset();
    }
  }

  draw(time) {
    const points = [];
    const cos = Math.cos(this.angle) * this.direction;
    const sin = Math.sin(this.angle);

    for (let i = 0; i < this.count; i += 1) {
      const waveOffset = Math.sin(this.phase + i * 0.72) * this.wave;
      const x = this.x + cos * this.spacing * i - sin * waveOffset;
      const y = this.y + sin * this.spacing * i + cos * waveOffset;
      points.push({ x, y });
    }

    ctx.save();
    ctx.lineCap = "round";
    ctx.shadowColor = this.color;
    ctx.shadowBlur = 4;

    for (let i = 1; i < points.length; i += 1) {
      const pulse = 0.55 + 0.45 * Math.sin(time * 2.2 + i * 0.75 + this.phase);
      ctx.beginPath();
      ctx.moveTo(points[i - 1].x, points[i - 1].y);
      ctx.lineTo(points[i].x, points[i].y);
      ctx.strokeStyle = hexToRgba(this.color, this.alpha * pulse);
      ctx.lineWidth = 2;
      ctx.stroke();
    }

    points.forEach((point, i) => {
      const pulse = 0.72 + 0.28 * Math.sin(time * 2.8 + i * 0.9 + this.phase);
      drawHex(point.x, point.y, this.radius * pulse, this.color, this.alpha * (0.75 + pulse));
    });

    ctx.restore();
  }
}

const particles = [];
const shapes = Array.from({ length: 4 }, () => new FloatingShape());
const hexChains = Array.from({ length: CHAIN_LANES.length }, (_, index) => new HexChain(index));
let lastTime = null;
let spawnTimer = 0;
let startRequested = false;
let menuReadySent = false;
let menuReadyAttempts = 0;
let inputHot = false;
let lastCanvasDraw = 0;
const creditsPanel = document.getElementById("credits-panel");
const creditsButton = document.getElementById("btn-credits");
const closeCreditsButton = document.getElementById("btn-close-credits");
const exitButton = document.getElementById("btn-exit");

function revealWhenFontsReady() {
  if (!document.fonts) {
    console.warn("[Fonts] document.fonts API not available");
    revealMenu();
    return;
  }

  console.log("[Fonts] Loading Ghora and MinimapCat...");
  Promise.all([
    document.fonts.load('72px "Ghora"'),
    document.fonts.load('24px "MinimapCat"'),
  ])
    .then(() => {
      console.log("[Fonts] Successfully loaded");
      const ghoraLoaded = document.fonts.check('72px "Ghora"');
      const minimapLoaded = document.fonts.check('24px "MinimapCat"');
      console.log(`[Fonts] Ghora available: ${ghoraLoaded}, MinimapCat available: ${minimapLoaded}`);
    })
    .catch((err) => console.error("[Fonts] Loading error:", err))
    .finally(revealMenu);

  window.setTimeout(revealMenu, 450);
}

revealWhenFontsReady();

function revealMenu() {
  document.body.classList.add("fonts-ready");
  window.setTimeout(notifyMenuReady, 0);
}

function notifyMenuReady() {
  if (menuReadySent) return;

  if (window.pywebview && window.pywebview.api && window.pywebview.api.menu_ready) {
    menuReadySent = true;
    window.pywebview.api.menu_ready().catch((err) => {
      console.error("[PyBridge] menu_ready hatasi:", err);
      menuReadySent = false;
      window.setTimeout(notifyMenuReady, 50);
    });
    return;
  }

  menuReadyAttempts += 1;
  if (menuReadyAttempts < 80) {
    window.setTimeout(notifyMenuReady, 50);
  } else {
    console.warn("[PyBridge] menu_ready icin pywebview.api beklenirken zaman asimi");
  }
}

function drawHex(x, y, radius, color, alpha) {
  ctx.beginPath();
  for (let i = 0; i < 6; i += 1) {
    const angle = Math.PI / 6 + (Math.PI / 3) * i;
    const px = x + Math.cos(angle) * radius;
    const py = y + Math.sin(angle) * radius;
    if (i === 0) {
      ctx.moveTo(px, py);
    } else {
      ctx.lineTo(px, py);
    }
  }
  ctx.closePath();
  ctx.strokeStyle = hexToRgba(color, alpha);
  ctx.lineWidth = 2;
  ctx.stroke();
  ctx.fillStyle = hexToRgba(color, alpha * 0.08);
  ctx.fill();
}

function drawCircuitLanes(time) {
  ctx.save();
  ctx.globalCompositeOperation = "lighter";

  GOLDEN_Y_RATIOS.forEach((ratio, index) => {
    const color = CATEGORY_COLORS[index % CATEGORY_COLORS.length];
    const y = SCREEN.H * ratio;
    const direction = index % 2 === 0 ? 1 : -1;
    const offset = (time * (28 + index * 5) * direction) % 220;
    const x0 = SCREEN.W * 0.055;
    const x1 = SCREEN.W * 0.945;
    const amp = SCREEN.H * 0.018;
    ctx.strokeStyle = hexToRgba(color, 0.055);
    ctx.lineWidth = 1;
    ctx.setLineDash([24, 44]);
    ctx.lineDashOffset = -offset;
    ctx.beginPath();
    ctx.moveTo(x0, y);
    ctx.bezierCurveTo(
      SCREEN.W * INV_PHI_SQ,
      y + Math.sin(time + index) * amp,
      SCREEN.W * INV_PHI,
      y - Math.cos(time * 0.8 + index) * amp * 1.25,
      x1,
      y + Math.sin(time * 0.6 + index) * amp,
    );
    ctx.stroke();
  });

  ctx.setLineDash([]);
  ctx.restore();
}

function animate(timestamp) {
  if (!lastTime) lastTime = timestamp;

  const frameInterval = inputHot ? 160 : 42;
  if (timestamp - lastCanvasDraw < frameInterval) {
    requestAnimationFrame(animate);
    return;
  }

  const dt = Math.min((timestamp - lastTime) / 1000, 0.08);
  lastTime = timestamp;
  lastCanvasDraw = timestamp;
  const time = timestamp / 1000;

  ctx.clearRect(0, 0, SCREEN.W, SCREEN.H);

  drawCircuitLanes(time);

  hexChains.forEach((chain) => {
    chain.update(dt);
    chain.draw(time);
  });

  spawnTimer += dt;
  if (spawnTimer > 0.12 && particles.length < MAX_PARTICLES) {
    particles.push(new Particle());
    spawnTimer = 0;
  }

  for (let i = particles.length - 1; i >= 0; i -= 1) {
    if (!particles[i].update(dt)) {
      particles.splice(i, 1);
    } else {
      particles[i].draw();
    }
  }

  shapes.forEach((shape) => {
    shape.update(dt);
    shape.draw();
  });

  requestAnimationFrame(animate);
}

requestAnimationFrame(animate);

function closestElement(target, selector) {
  return target instanceof Element ? target.closest(selector) : null;
}

document.addEventListener("pointerover", (event) => {
  if (closestElement(event.target, "button, .credits-panel")) {
    inputHot = true;
    document.body.classList.add("input-hot");
  }
});

document.addEventListener("pointerout", (event) => {
  if (!event.relatedTarget || !closestElement(event.relatedTarget, "button, .credits-panel")) {
    inputHot = false;
    document.body.classList.remove("input-hot");
  }
});

document.getElementById("btn-new-game").addEventListener("click", function createRipple(e) {
  const ripple = document.createElement("span");
  const rect = this.getBoundingClientRect();
  const size = Math.max(rect.width, rect.height);

  ripple.className = "ripple";
  ripple.style.cssText = `
    width:${size}px;
    height:${size}px;
    left:${e.clientX - rect.left - size / 2}px;
    top:${e.clientY - rect.top - size / 2}px;
  `;

  this.querySelector(".btn-ripple-container").appendChild(ripple);
  ripple.addEventListener("animationend", () => ripple.remove());
});

function startGame() {
  if (startRequested) return;
  startRequested = true;

  const button = document.getElementById("btn-new-game");
  button.disabled = true;

  const container = document.querySelector('.menu-container');
  container.style.transition = 'opacity 300ms ease';
  container.style.opacity = '0';

  setTimeout(() => {
    if (window.pywebview && window.pywebview.api) {
      window.pywebview.api.start_game().catch((err) => {
        console.error("[PyBridge] start_game hatasi:", err);
        startRequested = false;
        button.disabled = false;
        container.style.opacity = '1';
      });
    } else {
      console.warn("[PyBridge] pywebview.api bulunamadi - gelistirme modu");
      startRequested = false;
      button.disabled = false;
      container.style.opacity = '1';
    }
  }, 300);
}

function quitApp() {
  if (window.pywebview && window.pywebview.api) {
    window.pywebview.api.quit_app().catch((err) => {
      console.error("[PyBridge] quit_app hatasi:", err);
    });
  }
}

function openCredits() {
  creditsPanel.classList.add("open");
  creditsPanel.setAttribute("aria-hidden", "false");
  closeCreditsButton.focus();
}

function closeCredits() {
  creditsPanel.classList.remove("open");
  creditsPanel.setAttribute("aria-hidden", "true");
  creditsButton.focus();
}

creditsButton.addEventListener("click", openCredits);
closeCreditsButton.addEventListener("click", closeCredits);
exitButton.addEventListener("click", quitApp);

creditsPanel.addEventListener("click", (event) => {
  if (event.target === creditsPanel) closeCredits();
});

document.addEventListener("keydown", (event) => {
  if (event.key === "Escape") {
    if (creditsPanel.classList.contains("open")) {
      closeCredits();
      return;
    }
    quitApp();
  }
});
