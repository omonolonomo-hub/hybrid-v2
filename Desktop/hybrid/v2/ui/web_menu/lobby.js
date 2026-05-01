/**
 * Lobby screen with player configuration and strategy selection
 * Shared constants (CATEGORY_COLORS, DESIGN, hexToRgba) loaded from shared/canvas-utils.js
 */

const DEFAULT_STRATEGIES = [
  { id: "random", label: "Random", color: "#8C8C8C", description: "Unpredictable card purchases" },
  { id: "warrior", label: "Warrior", color: "#DC3C3C", description: "Aggressive combat focus" },
  { id: "builder", label: "Builder", color: "#50B464", description: "Synergy building strategy" },
  { id: "evolver", label: "Evolver", color: "#A05ADC", description: "Evolution-focused gameplay" },
  { id: "economist", label: "Economist", color: "#FFC832", description: "Gold optimization" },
  { id: "balancer", label: "Balancer", color: "#6496FF", description: "Balanced approach" },
  { id: "rare_hunter", label: "Rare Hunter", color: "#C8A0FF", description: "Targets rare cards" },
];

const DEFAULT_PLAYERS = [
  { kind: "ai", name: "AI 01", strategy: "random" },
  { kind: "ai", name: "AI 02", strategy: "warrior" },
  { kind: "ai", name: "AI 03", strategy: "builder" },
  { kind: "ai", name: "AI 04", strategy: "evolver" },
  { kind: "ai", name: "AI 05", strategy: "economist" },
  { kind: "ai", name: "AI 06", strategy: "balancer" },
  { kind: "ai", name: "AI 07", strategy: "rare_hunter" },
  { kind: "human", name: "HUMAN", strategy: "human" },
];

const SCREEN = { W: window.innerWidth, H: window.innerHeight };

const canvas = document.getElementById("lobby-canvas");
const ctx = canvas.getContext("2d");
const playerList = document.getElementById("player-list");
const counterValue = document.getElementById("counter-value");
const startButton = document.getElementById("btn-start-match");
const backButton = document.getElementById("btn-back");
const strategyLayer = document.getElementById("strategy-layer");

let players = DEFAULT_PLAYERS.map((player) => ({ ...player }));
let strategies = DEFAULT_STRATEGIES.map((strategy) => ({ ...strategy }));
let selectedStrategies = players.filter((player) => player.kind === "ai").map((player) => player.strategy);
let rowRefs = [];
let openDropdownIndex = null;
let openTrigger = null;
let activeOptionIndex = -1;
let lastTime = null;
let lastCanvasDraw = 0;
let lobbyReadySent = false;
let lobbyReadyAttempts = 0;
let lobbyLoaded = false;
let inputHot = false;

function resizeCanvas() {
  const dpr = 1;
  SCREEN.W = Math.max(window.innerWidth, 1);
  SCREEN.H = Math.max(window.innerHeight, 1);
  canvas.width = Math.round(SCREEN.W * dpr);
  canvas.height = Math.round(SCREEN.H * dpr);
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0);

  const scale = Math.min(SCREEN.W / DESIGN.W, SCREEN.H / DESIGN.H, 1);
  document.documentElement.style.setProperty("--ui-scale", scale.toFixed(4));
  closeStrategyMenu();
}

window.addEventListener("resize", resizeCanvas);
resizeCanvas();

class OrbitHex {
  constructor(index) {
    this.index = index;
    this.reset(true);
  }

  reset(initial = false) {
    this.color = CATEGORY_COLORS[this.index % CATEGORY_COLORS.length];
    this.radius = 13 + Math.random() * 15;
    this.x = initial ? Math.random() * SCREEN.W : -80 - Math.random() * 220;
    this.y = SCREEN.H * (0.18 + (this.index % 6) * 0.13) + (Math.random() - 0.5) * 36;
    this.speed = 14 + Math.random() * 18;
    this.spin = (Math.random() - 0.5) * 0.7;
    this.rotation = Math.random() * Math.PI * 2;
    this.alpha = 0.045 + Math.random() * 0.052;
  }

  update(dt) {
    this.x += this.speed * dt;
    this.y += Math.sin(this.x * 0.006 + this.index) * 3 * dt;
    this.rotation += this.spin * dt;
    if (this.x > SCREEN.W + 120) this.reset();
  }

  draw(time) {
    const pulse = 0.9 + Math.sin(time + this.index) * 0.08;
    // Only apply shadow to featured hexes (every 4th) to reduce GPU load
    const isFeatured = this.index % 4 === 0;
    drawHexLobby(ctx, this.x, this.y, this.radius * pulse, this.rotation, this.color, this.alpha, isFeatured);
  }
}

const orbitHexes = Array.from({ length: 12 }, (_, index) => new OrbitHex(index));

function drawConnectionGrid(time) {
  ctx.save();
  ctx.globalCompositeOperation = "lighter";
  ctx.lineWidth = 1;
  ctx.setLineDash([18, 44]);

  for (let i = 0; i < 6; i += 1) {
    const color = CATEGORY_COLORS[i % CATEGORY_COLORS.length];
    const y = SCREEN.H * (0.2 + i * 0.12);
    const pulse = (time * (18 + i * 3)) % 180;
    ctx.lineDashOffset = -pulse;
    ctx.strokeStyle = hexToRgba(color, 0.045);
    ctx.beginPath();
    ctx.moveTo(SCREEN.W * 0.11, y);
    ctx.bezierCurveTo(
      SCREEN.W * 0.34,
      y + Math.sin(time + i) * 20,
      SCREEN.W * 0.66,
      y - Math.cos(time * 0.8 + i) * 22,
      SCREEN.W * 0.89,
      y,
    );
    ctx.stroke();
  }

  ctx.setLineDash([]);
  ctx.restore();
}

function animate(timestamp) {
  if (!lastTime) lastTime = timestamp;

  const frameInterval = inputHot ? 140 : 42;
  if (timestamp - lastCanvasDraw >= frameInterval) {
    const dt = Math.min((timestamp - lastTime) / 1000, 0.08);
    lastTime = timestamp;
    const time = timestamp / 1000;
    ctx.clearRect(0, 0, SCREEN.W, SCREEN.H);
    drawConnectionGrid(time);
    orbitHexes.forEach((hex) => {
      hex.update(dt);
      hex.draw(time);
    });
    lastCanvasDraw = timestamp;
  }

  requestAnimationFrame(animate);
}

requestAnimationFrame(animate);

function getStrategyMeta(strategyId) {
  return strategies.find((strategy) => strategy.id === strategyId)
    || DEFAULT_STRATEGIES.find((strategy) => strategy.id === strategyId)
    || DEFAULT_STRATEGIES[0];
}

function setStrategyVars(element, color) {
  element.style.setProperty("--strategy-color", color);
  element.style.setProperty("--strategy-soft", hexToRgba(color, 0.14));
  element.style.setProperty("--strategy-glow", hexToRgba(color, 0.24));
  element.style.setProperty("--strategy-border", hexToRgba(color, 0.52));
}

function closestElement(target, selector) {
  return target instanceof Element ? target.closest(selector) : null;
}

function renderPlayers() {
  playerList.innerHTML = "";
  rowRefs = [];

  players.forEach((player, index) => {
    const row = player.kind === "human" ? createHumanRow(player, index) : createAiRow(player, index);
    playerList.appendChild(row);
  });
}

function createAiRow(player, index) {
  const meta = getStrategyMeta(player.strategy);
  const row = document.createElement("div");
  row.className = "player-row ai";
  row.dataset.index = String(index);
  row.style.animationDelay = `${index * 36}ms`;
  setStrategyVars(row, meta.color);

  row.appendChild(createPlayerMain(index, player.name));

  const strategyCell = document.createElement("div");
  strategyCell.className = "strategy-cell";

  const trigger = document.createElement("button");
  trigger.className = "strategy-trigger";
  trigger.type = "button";
  trigger.dataset.index = String(index);
  trigger.setAttribute("aria-haspopup", "listbox");
  trigger.setAttribute("aria-controls", "strategy-layer");
  trigger.setAttribute("aria-expanded", "false");
  trigger.innerHTML = `
    <span class="strategy-badge"></span>
    <span class="strategy-label">${meta.label}</span>
    <span class="trigger-arrow"></span>
  `;
  trigger.addEventListener("pointerdown", (event) => {
    event.preventDefault();
    event.stopPropagation();
    toggleStrategyMenu(index, trigger);
  });

  strategyCell.appendChild(trigger);
  row.appendChild(strategyCell);

  const profile = document.createElement("div");
  profile.className = "profile-text";
  profile.textContent = meta.description;
  row.appendChild(profile);

  rowRefs[index] = { row, trigger, label: trigger.querySelector(".strategy-label"), profile };
  return row;
}

function createHumanRow(player, index) {
  const row = document.createElement("div");
  row.className = "player-row human";
  row.style.animationDelay = `${index * 36}ms`;
  setStrategyVars(row, "#3CC864");
  row.appendChild(createPlayerMain(index, player.name));

  const strategyCell = document.createElement("div");
  strategyCell.className = "strategy-cell";
  strategyCell.innerHTML = `
    <button class="strategy-trigger" disabled
            aria-label="Human player - no strategy selection"
            title="Human player controls manually">
      <span class="strategy-badge"></span>
      <span>Human</span>
      <span></span>
    </button>
  `;
  row.appendChild(strategyCell);

  const profile = document.createElement("div");
  profile.className = "profile-text";
  profile.textContent = "Manual control";
  row.appendChild(profile);
  return row;
}

function createPlayerMain(index, name) {
  const main = document.createElement("div");
  main.className = "player-main";
  main.innerHTML = `
    <span class="slot-index">${String(index + 1).padStart(2, "0")}</span>
    <span class="player-name">${name}</span>
  `;
  return main;
}

function toggleStrategyMenu(index, trigger) {
  if (openDropdownIndex === index) {
    closeStrategyMenu();
    return;
  }

  openDropdownIndex = index;
  openTrigger = trigger;
  activeOptionIndex = Math.max(
    strategies.findIndex((strategy) => strategy.id === players[index].strategy),
    0,
  );
  rowRefs.forEach((ref) => ref?.trigger?.setAttribute("aria-expanded", "false"));
  trigger.setAttribute("aria-expanded", "true");
  buildStrategyLayer(index);
  positionStrategyLayer(trigger);
  strategyLayer.classList.add("open");
  strategyLayer.setAttribute("aria-hidden", "false");
  strategyLayer.focus();
  focusStrategyOption(activeOptionIndex);
}

function buildStrategyLayer(index) {
  const player = players[index];
  const meta = getStrategyMeta(player.strategy);
  setStrategyVars(strategyLayer, meta.color);
  strategyLayer.innerHTML = "";

  strategies.forEach((strategy) => {
    const option = document.createElement("button");
    option.className = `strategy-option${strategy.id === player.strategy ? " selected" : ""}`;
    option.type = "button";
    option.dataset.strategy = strategy.id;
    option.dataset.optionIndex = String(strategies.indexOf(strategy));
    option.id = `strategy-option-${index}-${strategies.indexOf(strategy)}`;
    option.setAttribute("role", "option");
    option.setAttribute("aria-selected", String(strategy.id === player.strategy));
    option.tabIndex = -1;
    option.style.setProperty("--option-color", strategy.color);
    option.style.setProperty("--option-soft", hexToRgba(strategy.color, 0.18));
    option.innerHTML = `
      <span class="strategy-badge"></span>
      <span>${strategy.label}</span>
    `;
    option.addEventListener("pointerdown", (event) => {
      event.preventDefault();
      event.stopPropagation();
      selectStrategy(index, strategy.id);
    });
    strategyLayer.appendChild(option);
  });
}

function positionStrategyLayer(trigger) {
  const rect = trigger.getBoundingClientRect();
  const menuWidth = 242;
  const menuHeight = 282;
  const gap = 8;
  const left = Math.min(Math.max(rect.left, 12), window.innerWidth - menuWidth - 12);
  const shouldOpenUp = rect.bottom + gap + menuHeight > window.innerHeight - 16;
  const top = shouldOpenUp
    ? Math.max(12, rect.top - menuHeight - gap)
    : rect.bottom + gap;

  strategyLayer.style.left = `${left}px`;
  strategyLayer.style.top = `${top}px`;
}

function closeStrategyMenu() {
  if (openTrigger) openTrigger.setAttribute("aria-expanded", "false");
  openDropdownIndex = null;
  openTrigger = null;
  activeOptionIndex = -1;
  strategyLayer.classList.remove("open");
  strategyLayer.setAttribute("aria-hidden", "true");
  strategyLayer.removeAttribute("aria-activedescendant");
}

function focusStrategyOption(index) {
  const options = getStrategyOptions();
  if (!options.length) return;

  activeOptionIndex = (index + options.length) % options.length;
  options.forEach((option, optionIndex) => {
    const isActive = optionIndex === activeOptionIndex;
    option.classList.toggle("keyboard-focus", isActive);
    option.tabIndex = isActive ? 0 : -1;
  });
  strategyLayer.setAttribute("aria-activedescendant", options[activeOptionIndex].id);
  options[activeOptionIndex].focus();
}

function getStrategyOptions() {
  return Array.from(strategyLayer.querySelectorAll(".strategy-option"));
}

function moveStrategyFocus(step) {
  const options = getStrategyOptions();
  if (!options.length) return;
  focusStrategyOption(activeOptionIndex + step);
}

function chooseFocusedStrategy() {
  const options = getStrategyOptions();
  const option = options[activeOptionIndex];
  if (!option || openDropdownIndex === null) return;
  selectStrategy(openDropdownIndex, option.dataset.strategy);
}

function selectStrategy(index, strategyId) {
  const player = players[index];
  if (!player || player.kind !== "ai") return;

  player.strategy = strategyId;
  selectedStrategies[index] = strategyId;
  updateAiRow(index);
  const trigger = openTrigger;
  closeStrategyMenu();
  if (trigger) trigger.focus();

  if (window.pywebview && window.pywebview.api && window.pywebview.api.set_strategy) {
    window.pywebview.api.set_strategy(index, strategyId).catch((err) => {
      console.error("[PyBridge] set_strategy error:", err);
    });
  }
}

function updateAiRow(index) {
  const ref = rowRefs[index];
  if (!ref) return;

  const meta = getStrategyMeta(players[index].strategy);
  setStrategyVars(ref.row, meta.color);
  ref.label.textContent = meta.label;
  ref.profile.textContent = meta.description;
}

function animateCounter(target) {
  const start = performance.now();
  const duration = 620;

  function tick(now) {
    const progress = Math.min((now - start) / duration, 1);
    const eased = 1 - Math.pow(1 - progress, 3);
    counterValue.textContent = String(Math.round(target * eased));
    if (progress < 1) requestAnimationFrame(tick);
  }

  requestAnimationFrame(tick);
}

function revealLobby() {
  renderPlayers();
  document.body.classList.add("lobby-ready");
  animateCounter(players.length);
  window.setTimeout(notifyLobbyReady, 0);
}

function notifyLobbyReady() {
  if (lobbyReadySent) return;

  if (window.pywebview && window.pywebview.api && window.pywebview.api.lobby_ready) {
    lobbyReadySent = true;
    window.pywebview.api.lobby_ready().catch((err) => {
      console.error("[PyBridge] lobby_ready error:", err);
      lobbyReadySent = false;
      window.setTimeout(notifyLobbyReady, 50);
    });
    return;
  }

  lobbyReadyAttempts += 1;
  if (lobbyReadyAttempts < 80) window.setTimeout(notifyLobbyReady, 50);
}

function loadLobbyState() {
  if (lobbyLoaded) return;
  lobbyLoaded = true;

  if (!window.pywebview || !window.pywebview.api || !window.pywebview.api.get_lobby_state) {
    revealLobby();
    return;
  }

  window.pywebview.api.get_lobby_state()
    .then((state) => {
      if (state && Array.isArray(state.strategies)) strategies = state.strategies;
      if (state && Array.isArray(state.players)) players = state.players;
      selectedStrategies = players.filter((player) => player.kind === "ai").map((player) => player.strategy);
    })
    .catch((err) => console.error("[PyBridge] get_lobby_state error:", err))
    .finally(revealLobby);
}

function waitForFontsThenLoad() {
  if (!document.fonts) {
    loadLobbyState();
    return;
  }

  Promise.all([
    document.fonts.load('68px "Ghora"'),
    document.fonts.load('16px "Butler"'),
  ])
    .catch((err) => console.warn("[Fonts] lobby font warning:", err))
    .finally(loadLobbyState);

  window.setTimeout(loadLobbyState, 420);
}

startButton.addEventListener("click", () => {
  if (startButton.disabled) return;
  startButton.disabled = true;
  startButton.classList.add("loading");
  closeStrategyMenu();

  if (window.pywebview && window.pywebview.api && window.pywebview.api.start_match) {
    window.pywebview.api.start_match(selectedStrategies).catch((err) => {
      console.error("[PyBridge] start_match error:", err);
      startButton.disabled = false;
      startButton.classList.remove("loading");
    });
  } else {
    console.warn("[PyBridge] start_match unavailable");
    startButton.disabled = false;
    startButton.classList.remove("loading");
  }
});

backButton.addEventListener("click", () => {
  closeStrategyMenu();
  if (window.pywebview && window.pywebview.api && window.pywebview.api.back_to_menu) {
    window.pywebview.api.back_to_menu().catch((err) => {
      console.error("[PyBridge] back_to_menu error:", err);
    });
  }
});

document.addEventListener("pointerdown", (event) => {
  if (!strategyLayer.contains(event.target) && !closestElement(event.target, ".strategy-trigger")) {
    closeStrategyMenu();
  }
});

document.addEventListener("pointerover", (event) => {
  if (closestElement(event.target, "button, .player-row, .strategy-layer")) {
    inputHot = true;
    document.body.classList.add("input-hot");
  }
});

document.addEventListener("pointerout", (event) => {
  if (!event.relatedTarget || !closestElement(event.relatedTarget, "button, .player-row, .strategy-layer")) {
    inputHot = false;
    document.body.classList.remove("input-hot");
  }
});

document.addEventListener("keydown", (event) => {
  if (openDropdownIndex !== null) {
    if (event.key === "ArrowDown" || (event.key === "Tab" && !event.shiftKey)) {
      event.preventDefault();
      moveStrategyFocus(1);
      return;
    }
    if (event.key === "ArrowUp" || (event.key === "Tab" && event.shiftKey)) {
      event.preventDefault();
      moveStrategyFocus(-1);
      return;
    }
    if (event.key === "Home") {
      event.preventDefault();
      focusStrategyOption(0);
      return;
    }
    if (event.key === "End") {
      event.preventDefault();
      focusStrategyOption(getStrategyOptions().length - 1);
      return;
    }
    if (event.key === "Enter" || event.key === " ") {
      event.preventDefault();
      chooseFocusedStrategy();
      return;
    }
  }

  if (event.key === "Escape") {
    if (openDropdownIndex !== null) {
      const trigger = openTrigger;
      closeStrategyMenu();
      if (trigger) trigger.focus();
      return;
    }
    if (window.pywebview && window.pywebview.api) {
      window.pywebview.api.quit_app().catch((err) => {
        console.error("[PyBridge] quit_app error:", err);
      });
    }
  }
});

waitForFontsThenLoad();
