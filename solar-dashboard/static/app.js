/* NRG Command Center — frontend */

const COLORS = {
  solar: "#eda100",
  battery: "#1baf7a",
  home: "#9085e9",
  grid: "#3987e5",
  export: "#d55181",
  ink2: "#c3c2b7",
  muted: "#898781",
  gridline: "#2c2c2a",
};

const $ = (id) => document.getElementById(id);
const fmtW = (w) => {
  const a = Math.abs(w);
  return a >= 1000 ? `${(w / 1000).toFixed(2)}<small> kW</small>` : `${Math.round(w)}<small> W</small>`;
};
const fmtKw = (w) => (Math.abs(w) >= 1000 ? `${(w / 1000).toFixed(2)} kW` : `${Math.round(w)} W`);
let CUR = "$";
const money = (v) => `${v < 0 ? "−" : ""}${CUR}${Math.abs(v).toFixed(2)}`;

async function api(path, opts) {
  const r = await fetch(path, opts);
  if (!r.ok) throw new Error(`${path} → ${r.status}`);
  return r.json();
}

/* ---------- house scene (live power flow) ----------
   Default: illustrated isometric night house.
   Photo mode: put house.jpg + scene.json in static/ (see scene.example.json)
   and the chips/flows render over your real house instead. */

const NS = "http://www.w3.org/2000/svg";
const flowEls = {};

function el(name, attrs, parent) {
  const e = document.createElementNS(NS, name);
  for (const [k, v] of Object.entries(attrs)) e.setAttribute(k, v);
  parent.appendChild(e);
  return e;
}

// roof surface parametrization: s along front-left edge, t along back-left edge
const ROOF = { o: [280, 208], u: [140, 60], v: [140, -60] };
const roofPt = (s, t) => [
  ROOF.o[0] + ROOF.u[0] * s + ROOF.v[0] * t,
  ROOF.o[1] + ROOF.u[1] * s + ROOF.v[1] * t,
];
const poly = (pts) => pts.map((p) => p.join(",")).join(" ");

function buildDefs(svg) {
  const defs = el("defs", {}, svg);
  const sky = el("radialGradient", { id: "sky", cx: "50%", cy: "20%", r: "90%" }, defs);
  el("stop", { offset: "0%", "stop-color": "#31245c" }, sky);
  el("stop", { offset: "55%", "stop-color": "#1c1836" }, sky);
  el("stop", { offset: "100%", "stop-color": "#100e1e" }, sky);
  const glow = el("filter", { id: "glow", x: "-60%", y: "-60%", width: "220%", height: "220%" }, defs);
  el("feGaussianBlur", { stdDeviation: "3.2", result: "b" }, glow);
  const m = el("feMerge", {}, glow);
  el("feMergeNode", { in: "b" }, m);
  el("feMergeNode", { in: "SourceGraphic" }, m);
}

function buildHouse(svg) {
  const g = el("g", {}, svg);
  // stars
  const rng = (n) => (Math.sin(n * 127.1) * 43758.5453) % 1;
  for (let i = 0; i < 42; i++) {
    const x = Math.abs(rng(i)) * 790 + 5, y = Math.abs(rng(i + 99)) * 190 + 8;
    el("circle", { cx: x, cy: y, r: Math.abs(rng(i + 7)) * 1.1 + 0.3, fill: "#cdc8ff", opacity: (0.15 + Math.abs(rng(i + 31)) * 0.4).toFixed(2) }, g);
  }
  el("circle", { cx: 706, cy: 64, r: 22, fill: "#e8e4ff", opacity: 0.85, filter: "url(#glow)" }, g); // moon
  el("ellipse", { cx: 420, cy: 392, rx: 330, ry: 58, fill: "rgba(180,170,255,0.045)" }, g); // ground

  // walls  (footprint F(280,330) C(420,390) R(560,330) B(420,270), height 90)
  el("polygon", { points: "280,330 420,390 420,300 280,240", fill: "#232338", stroke: "#3a3a58", "stroke-width": 1 }, g); // left
  el("polygon", { points: "420,390 560,330 560,240 420,300", fill: "#2c2c46", stroke: "#3a3a58", "stroke-width": 1 }, g); // right
  // roof slab (slightly proud of the walls)
  el("polygon", { points: poly([roofPt(-0.06, -0.06), roofPt(1.06, -0.06), roofPt(1.06, 1.06), roofPt(-0.06, 1.06)]), fill: "#1d1d32", stroke: "#44446a", "stroke-width": 1.2 }, g);

  // solar array — 3 rows × 4 cols on the roof (Dave's near-flat mount)
  flowEls.panels = el("g", {}, g);
  for (let r = 0; r < 3; r++) {
    for (let c = 0; c < 4; c++) {
      const s0 = 0.08 + c * 0.215, t0 = 0.12 + r * 0.27;
      el("polygon", {
        points: poly([roofPt(s0, t0), roofPt(s0 + 0.19, t0), roofPt(s0 + 0.19, t0 + 0.23), roofPt(s0, t0 + 0.23)]),
        fill: "#14315c", stroke: "#3987e5", "stroke-width": 0.8, opacity: 0.9,
      }, flowEls.panels);
    }
  }

  // door + windows (windows glow with house load)
  el("polygon", { points: "388,362 412,372 412,318 388,308", fill: "#191928", stroke: "#3a3a58" }, g);
  flowEls.windows = el("g", {}, g);
  el("polygon", { points: "300,308 336,323 336,285 300,270", fill: "#ffb84d", stroke: "#3a3a58" }, flowEls.windows);
  el("polygon", { points: "455,345 500,326 500,288 455,307", fill: "#ffb84d", stroke: "#3a3a58" }, flowEls.windows);
  flowEls.windows.style.opacity = 0.25;
  flowEls.windows.style.filter = "url(#glow)";
  flowEls.windows.style.transition = "opacity 1s";

  // battery cabinet (right of house)
  el("polygon", { points: "612,310 640,324 668,310 640,296", fill: "#20203a", stroke: "#3a3a58" }, g);
  el("polygon", { points: "612,310 640,324 640,368 612,354", fill: "#191930", stroke: "#3a3a58" }, g);
  el("polygon", { points: "640,324 668,310 668,354 640,368", fill: "#242442", stroke: "#3a3a58" }, g);
  flowEls.battLed = el("polygon", { points: "646,327 662,335 662,340 646,332", fill: COLORS.battery, filter: "url(#glow)" }, g);

  // power pole (left)
  el("line", { x1: 110, y1: 150, x2: 110, y2: 368, stroke: "#4a4a68", "stroke-width": 5, "stroke-linecap": "round" }, g);
  el("line", { x1: 82, y1: 172, x2: 138, y2: 172, stroke: "#4a4a68", "stroke-width": 4, "stroke-linecap": "round" }, g);
  el("line", { x1: 88, y1: 196, x2: 132, y2: 196, stroke: "#4a4a68", "stroke-width": 3.5, "stroke-linecap": "round" }, g);
  el("circle", { cx: 96, cy: 168, r: 2.5, fill: "#8a86c9" }, g);
  el("circle", { cx: 124, cy: 168, r: 2.5, fill: "#8a86c9" }, g);
  el("path", { d: "M 124 172 Q 200 235 281 246", fill: "none", stroke: "#3d3d5c", "stroke-width": 1.6 }, g); // service wire
}

// scene geometry: flow paths + chip positions (illustrated default)
const DEFAULT_SCENE = {
  photo: null,
  flows: {
    grid:    "M 124 172 Q 200 235 281 246",
    solar:   "M 400 226 C 410 250 415 265 418 292",
    battery: "M 626 332 C 585 330 570 315 545 300",
    home:    "M 420 320 C 400 345 360 372 300 386",
  },
  chips: {
    solar:   { x: 452, y: 96,  anchor: [420, 208] },
    grid:    { x: 30,  y: 84,  anchor: [110, 155] },
    battery: { x: 636, y: 196, anchor: [648, 300] },
    home:    { x: 176, y: 396, anchor: [300, 386] },
  },
};

function buildChip(svg, key, label, cfg) {
  const g = el("g", { class: "chip" }, svg);
  el("line", { x1: cfg.x + 74, y1: cfg.y + 46, x2: cfg.anchor[0], y2: cfg.anchor[1], stroke: "rgba(200,195,255,0.25)", "stroke-width": 1, "stroke-dasharray": "2 3" }, g);
  el("rect", { x: cfg.x, y: cfg.y, width: 148, height: 46, rx: 13, fill: "rgba(16,15,30,0.82)", stroke: "rgba(200,195,255,0.22)", "stroke-width": 1 }, g);
  el("circle", { cx: cfg.x + 15, cy: cfg.y + 23, r: 4, fill: COLORS[key], filter: "url(#glow)" }, g);
  flowEls[key + "Val"] = el("text", { x: cfg.x + 27, y: cfg.y + 20, class: "chip-value" }, g);
  flowEls[key + "Sub"] = el("text", { x: cfg.x + 27, y: cfg.y + 36, class: "chip-sub" }, g);
  flowEls[key + "Sub"].textContent = label;
}

let scene3d = null;                       // loaded 3D module (or null)
let flowView = localStorage.getItem("flowView") || "3d";
let hasCustomScene = false;

async function initFlowView() {
  await buildFlow();                      // SVG scene always available
  if (hasCustomScene && !localStorage.getItem("flowView")) flowView = "2d";
  if (flowView === "3d") {
    try {
      const mod = await import("/static/scene3d.js");
      if (mod.isSupported()) {
        mod.init($("scene3d"));
        scene3d = mod;
      }
    } catch (e) { console.warn("3D scene unavailable, using 2D:", e); }
  }
  if (!scene3d) flowView = "2d";
  applyFlowView();
  $("btn-view").addEventListener("click", async () => {
    if (flowView === "2d" && !scene3d) {
      try {
        const mod = await import("/static/scene3d.js");
        if (mod.isSupported()) { mod.init($("scene3d")); scene3d = mod; }
      } catch (e) { return; }
      if (!scene3d) return;
    }
    flowView = flowView === "3d" ? "2d" : "3d";
    localStorage.setItem("flowView", flowView);
    applyFlowView();
    if (lastSnap) updateFlow(lastSnap);
  });
}

function applyFlowView() {
  const is3d = flowView === "3d" && !!scene3d;
  $("scene3d").classList.toggle("hidden", !is3d);
  $("flow").classList.toggle("hidden", is3d);
  $("btn-view").textContent = is3d ? "2D view" : "3D view";
  if (scene3d) scene3d.setActive(is3d);
}

async function buildFlow() {
  const svg = $("flow");
  buildDefs(svg);

  let scene = DEFAULT_SCENE;
  try {
    const custom = await api("/api/scene");
    if (custom) { scene = { ...DEFAULT_SCENE, ...custom }; hasCustomScene = true; }
  } catch (e) { /* no custom scene — use illustration */ }

  el("rect", { x: 0, y: 0, width: 800, height: 460, rx: 14, fill: "url(#sky)" }, svg);
  if (scene.photo) {
    el("image", { href: scene.photo, x: 0, y: 0, width: 800, height: 460, preserveAspectRatio: "xMidYMid slice", opacity: 0.92 }, svg);
    el("rect", { x: 0, y: 0, width: 800, height: 460, rx: 14, fill: "rgba(10,8,24,0.35)" }, svg);
  } else {
    buildHouse(svg);
  }

  for (const [k, d] of Object.entries(scene.flows)) {
    el("path", { d, class: "flow-under", stroke: COLORS[k === "grid" ? "grid" : k] }, svg);
    flowEls[k] = el("path", { d, class: "flowline", stroke: COLORS[k === "grid" ? "grid" : k] }, svg);
  }
  buildChip(svg, "solar", "SOLAR", scene.chips.solar);
  buildChip(svg, "grid", "GRID", scene.chips.grid);
  buildChip(svg, "battery", "BATTERY", scene.chips.battery);
  buildChip(svg, "home", "LOAD", scene.chips.home);
}

function setFlow(key, watts, reverse) {
  const line = flowEls[key];
  const under = line.previousSibling;
  const on = Math.abs(watts) > 40;
  line.classList.toggle("on", on);
  under.classList.toggle("on", on);
  line.classList.toggle("rev", !!reverse);
  line.style.strokeWidth = (2 + Math.min(3, Math.abs(watts) / 1600)).toFixed(1);
  line.style.animationDuration = `${Math.max(0.4, 1.5 - Math.abs(watts) / 4500)}s`;
}

let lastSnap = null;

function updateFlow(s) {
  lastSnap = s;
  if (scene3d && flowView === "3d") scene3d.update(s);
  flowEls.solarVal.textContent = fmtKw(s.ppv);
  flowEls.batteryVal.textContent = `${s.soc.toFixed(0)}%  ${
    s.pbat < -40 ? "▲ " + fmtKw(-s.pbat) : s.pbat > 40 ? "▼ " + fmtKw(s.pbat) : "idle"}`;
  flowEls.homeVal.textContent = fmtKw(s.pload);
  flowEls.gridVal.textContent = `${fmtKw(Math.abs(s.pgrid))} ${
    s.pgrid > 40 ? "in" : s.pgrid < -40 ? "out" : ""}`;

  setFlow("solar", s.ppv, false);            // panels → house
  setFlow("battery", s.pbat, s.pbat < 0);    // battery ↔ house
  setFlow("home", s.pload, false);           // house → loads
  setFlow("grid", s.pgrid, s.pgrid < 0);     // pole ↔ house

  if (flowEls.windows) flowEls.windows.style.opacity = Math.min(0.95, 0.12 + s.pload / 3000);
  if (flowEls.panels) flowEls.panels.style.opacity = s.ppv > 20 ? 1 : 0.55;
  if (flowEls.battLed) flowEls.battLed.setAttribute("fill", s.pbat < -40 ? COLORS.battery : s.pbat > 40 ? COLORS.solar : "#4a4a68");
}

/* ---------- tiles ---------- */

function updateTiles(s) {
  $("v-solar").innerHTML = fmtW(s.ppv);
  $("s-solar").textContent = s.ppv > 20 ? "☀ generating" : "offline until sunrise";
  $("v-batt").innerHTML = `${s.soc.toFixed(0)}<small> %</small>`;
  $("socfill").style.width = `${s.soc}%`;
  $("s-batt").textContent =
    s.pbat < -40 ? `charging at ${fmtKw(-s.pbat)}` :
    s.pbat > 40 ? `discharging at ${fmtKw(s.pbat)}` : "idle";
  $("v-home").innerHTML = fmtW(s.pload);
  $("s-home").textContent = "current draw";
  $("v-grid").innerHTML = fmtW(Math.abs(s.pgrid));
  $("s-grid").textContent =
    s.pgrid > 40 ? "importing — costing money" :
    s.pgrid < -40 ? "exporting — earning FiT" : "balanced";
  $("last-update").textContent = `updated ${new Date().toLocaleTimeString()}`;
}

/* ---------- charts ---------- */

let chToday, chSoc, chHist;

function chartDefaults() {
  Chart.defaults.color = COLORS.muted;
  Chart.defaults.borderColor = COLORS.gridline;
  Chart.defaults.font.family = 'system-ui, -apple-system, "Segoe UI", sans-serif';
  Chart.defaults.font.size = 11;
  Chart.defaults.plugins.legend.labels.boxWidth = 9;
  Chart.defaults.plugins.legend.labels.boxHeight = 9;
  Chart.defaults.plugins.legend.labels.usePointStyle = true;
  Chart.defaults.plugins.tooltip.backgroundColor = "#222220";
  Chart.defaults.plugins.tooltip.borderColor = "rgba(255,255,255,0.12)";
  Chart.defaults.plugins.tooltip.borderWidth = 1;
  Chart.defaults.animation.duration = 400;
}

const hhmm = (ts) => ts.slice(11, 16);

function lineDs(label, color, data, fill = false) {
  return {
    label, data, borderColor: color, backgroundColor: color + "22",
    borderWidth: 2, pointRadius: 0, pointHoverRadius: 4, tension: 0.3,
    fill: fill ? "origin" : false, spanGaps: true,
  };
}

function buildToday(rows) {
  const labels = rows.map((r) => hhmm(r.ts));
  const cfg = {
    type: "line",
    data: {
      labels,
      datasets: [
        lineDs("Solar", COLORS.solar, rows.map((r) => r.ppv), true),
        lineDs("Home", COLORS.home, rows.map((r) => r.pload)),
        lineDs("Grid", COLORS.grid, rows.map((r) => r.pgrid)),
        lineDs("Battery", COLORS.battery, rows.map((r) => r.pbat)),
      ],
    },
    options: {
      responsive: true, maintainAspectRatio: false,
      interaction: { mode: "index", intersect: false },
      scales: {
        x: { ticks: { maxTicksLimit: 13, maxRotation: 0 }, grid: { display: false } },
        y: {
          ticks: { callback: (v) => `${v / 1000} kW` },
          grid: { color: COLORS.gridline },
        },
      },
      plugins: {
        tooltip: { callbacks: { label: (c) => ` ${c.dataset.label}: ${fmtKw(c.parsed.y)}` } },
      },
    },
  };
  if (chToday) { chToday.data = cfg.data; chToday.update(); return; }
  chToday = new Chart($("chart-today"), cfg);
}

function buildSoc(rows) {
  const cfg = {
    type: "line",
    data: {
      labels: rows.map((r) => hhmm(r.ts)),
      datasets: [{
        ...lineDs("State of charge", COLORS.battery, rows.map((r) => r.soc), true),
      }],
    },
    options: {
      responsive: true, maintainAspectRatio: false,
      interaction: { mode: "index", intersect: false },
      scales: {
        x: { ticks: { maxTicksLimit: 7, maxRotation: 0 }, grid: { display: false } },
        y: { min: 0, max: 100, ticks: { callback: (v) => v + "%" }, grid: { color: COLORS.gridline } },
      },
      plugins: {
        legend: { display: false },
        tooltip: { callbacks: { label: (c) => ` SOC: ${c.parsed.y.toFixed(0)}%` } },
      },
    },
  };
  if (chSoc) { chSoc.data = cfg.data; chSoc.update(); return; }
  chSoc = new Chart($("chart-soc"), cfg);
}

function barDs(label, color, data) {
  return {
    label, data, backgroundColor: color, borderRadius: 4,
    borderSkipped: "bottom", maxBarThickness: 16,
  };
}

function buildHistory(rows) {
  const labels = rows.map((r) =>
    new Date(r.date + "T00:00").toLocaleDateString(undefined, { day: "numeric", month: "short" }));
  const cfg = {
    type: "bar",
    data: {
      labels,
      datasets: [
        barDs("Generated", COLORS.solar, rows.map((r) => r.epv)),
        barDs("Home used", COLORS.home, rows.map((r) => r.eload)),
        barDs("Grid import", COLORS.grid, rows.map((r) => r.einput)),
        barDs("Exported", COLORS.export, rows.map((r) => r.eoutput)),
      ],
    },
    options: {
      responsive: true, maintainAspectRatio: false,
      scales: {
        x: { grid: { display: false } },
        y: { ticks: { callback: (v) => v + " kWh" }, grid: { color: COLORS.gridline } },
      },
      plugins: {
        tooltip: { callbacks: { label: (c) => ` ${c.dataset.label}: ${c.parsed.y.toFixed(1)} kWh` } },
      },
    },
  };
  if (chHist) { chHist.data = cfg.data; chHist.update(); return; }
  chHist = new Chart($("chart-history"), cfg);
}

/* ---------- money / tariff ---------- */

let tariffCache = null;

function describeTariff(t) {
  if (t.mode === "tou") {
    return "TOU: " + t.tou.map((w) => `${w.name} ${CUR}${(+w.rate).toFixed(2)}`).join(" · ")
      + ` · FiT ${CUR}${(+t.feed_in).toFixed(2)}`;
  }
  return `Flat ${CUR}${(+t.flat_import).toFixed(2)}/kWh · FiT ${CUR}${(+t.feed_in).toFixed(2)}/kWh`;
}

async function refreshMoney() {
  const s = await api("/api/savings");
  tariffCache = s.tariff;
  CUR = s.tariff.currency || "$";
  $("m-today").textContent = money(s.today.saved);
  $("m-week").textContent = money(s.week_saved);
  $("m-annual").textContent = `≈ ${CUR}${Math.round(s.annual_projection).toLocaleString()}/yr`;
  $("m-export").textContent = money(s.today.export_earned);
  $("m-tariff-desc").textContent = describeTariff(s.tariff);
}

function openTariffModal() {
  const t = tariffCache || { mode: "flat", flat_import: 0.32, feed_in: 0.05, tou: [] };
  $("t-mode").value = t.mode;
  $("t-flat").value = (+t.flat_import).toFixed(2);
  $("t-fit").value = (+t.feed_in).toFixed(2);
  const wrap = $("tou-rows");
  wrap.querySelectorAll(".tou-edit").forEach((e) => e.remove());
  (t.tou || []).forEach((w, i) => {
    const row = document.createElement("div");
    row.className = "tou-row tou-edit";
    row.innerHTML = `
      <input type="text" value="${w.name}" data-i="${i}" data-k="name">
      <input type="time" value="${w.start}" data-i="${i}" data-k="start">
      <input type="time" value="${w.end === "24:00" ? "23:59" : w.end}" data-i="${i}" data-k="end">
      <input type="number" step="0.01" min="0" value="${(+w.rate).toFixed(2)}" data-i="${i}" data-k="rate">`;
    wrap.appendChild(row);
  });
  wrap.classList.toggle("hidden", t.mode !== "tou");
  $("tariff-modal").showModal();
}

async function saveTariff() {
  const t = {
    mode: $("t-mode").value,
    flat_import: parseFloat($("t-flat").value) || 0.32,
    feed_in: parseFloat($("t-fit").value) || 0,
    currency: CUR,
    tou: [],
  };
  document.querySelectorAll("#tou-rows .tou-edit").forEach((row) => {
    const g = (k) => row.querySelector(`[data-k="${k}"]`).value;
    t.tou.push({ name: g("name"), start: g("start"), end: g("end"), rate: parseFloat(g("rate")) || 0 });
  });
  await api("/api/tariff", {
    method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(t),
  });
  await refreshMoney();
  await refreshHistory();
}

/* ---------- battery config ---------- */

const lc = (o) => Object.fromEntries(Object.entries(o || {}).map(([k, v]) => [k.toLowerCase(), v]));
const t5 = (v) => (typeof v === "string" && v.length >= 5 ? v.slice(0, 5) : "00:00");

async function refreshBatteryConfig() {
  const cfg = await api("/api/battery-config");
  const c = lc(cfg.charge), d = lc(cfg.discharge);
  $("bc-gridCharge").checked = !!+(c.gridcharge ?? 0);
  $("bc-chaf1").value = t5(c.timechaf1); $("bc-chae1").value = t5(c.timechae1);
  $("bc-chaf2").value = t5(c.timechaf2); $("bc-chae2").value = t5(c.timechae2);
  $("bc-batHighCap").value = +(c.bathighcap ?? 100);
  $("bc-ctrDis").checked = !!+(d.ctrdis ?? 0);
  $("bc-disf1").value = t5(d.timedisf1); $("bc-dise1").value = t5(d.timedise1);
  $("bc-disf2").value = t5(d.timedisf2); $("bc-dise2").value = t5(d.timedise2);
  $("bc-batUseCap").value = +(d.batusecap ?? 10);
}

async function saveBatteryConfig(ev) {
  ev.preventDefault();
  const body = {
    charge: {
      gridCharge: $("bc-gridCharge").checked ? 1 : 0,
      batHighCap: parseFloat($("bc-batHighCap").value) || 100,
      timeChaf1: $("bc-chaf1").value || "00:00", timeChae1: $("bc-chae1").value || "00:00",
      timeChaf2: $("bc-chaf2").value || "00:00", timeChae2: $("bc-chae2").value || "00:00",
    },
    discharge: {
      ctrDis: $("bc-ctrDis").checked ? 1 : 0,
      batUseCap: parseFloat($("bc-batUseCap").value) || 10,
      timeDisf1: $("bc-disf1").value || "00:00", timeDise1: $("bc-dise1").value || "00:00",
      timeDisf2: $("bc-disf2").value || "00:00", timeDise2: $("bc-dise2").value || "00:00",
    },
  };
  const note = $("batt-note");
  note.textContent = "applying…";
  try {
    const r = await api("/api/battery-config", {
      method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body),
    });
    note.textContent = r.mode === "demo"
      ? "saved locally (demo mode — nothing sent to your inverter)"
      : "✓ applied to your system via AlphaESS";
  } catch (e) {
    note.textContent = "failed: " + e.message;
  }
}

/* ---------- insights / status ---------- */

async function refreshInsights() {
  const tips = await api("/api/insights");
  const ul = $("insights");
  ul.innerHTML = "";
  for (const t of tips) {
    const li = document.createElement("li");
    const tag = { tip: "TIP", stat: "STAT", warn: "WATCH" }[t.level] || "INFO";
    li.innerHTML = `<span class="tag ${t.level}">${tag}</span><span></span>`;
    li.lastElementChild.textContent = t.text;
    ul.appendChild(li);
  }
}

async function refreshStatus() {
  const st = await api("/api/status");
  const badge = $("mode-badge");
  badge.textContent = st.mode === "demo" ? "DEMO DATA" : "● LIVE";
  badge.className = "badge " + st.mode;
  $("sys-sn").textContent = st.sn;
  $("f-mode").textContent = st.mode === "demo"
    ? "Demo mode — add AlphaESS credentials to .env to go live"
    : `Live · polling every ${st.poll_interval}s`;
  $("f-poll").textContent = st.last_poll ? `last poll ${st.last_poll.slice(11, 19)}` : "";
  $("f-err").textContent = st.last_error ? `⚠ ${st.last_error}` : "";
}

/* ---------- refresh loops ---------- */

async function refreshLive() {
  try {
    const s = await api("/api/live");
    updateFlow(s);
    updateTiles(s);
  } catch (e) { /* poller warming up */ }
}

async function refreshCharts() {
  const rows = await api("/api/today");
  if (rows.length) { buildToday(rows); buildSoc(rows); }
}

async function refreshHistory() {
  const rows = await api("/api/history?days=14");
  if (rows.length) buildHistory(rows);
}

function tickClock() {
  $("clock").textContent = new Date().toLocaleString(undefined,
    { weekday: "short", hour: "2-digit", minute: "2-digit", second: "2-digit" });
}

async function init() {
  chartDefaults();
  await initFlowView();
  tickClock(); setInterval(tickClock, 1000);

  $("btn-tariff").addEventListener("click", openTariffModal);
  $("t-mode").addEventListener("change", () =>
    $("tou-rows").classList.toggle("hidden", $("t-mode").value !== "tou"));
  $("tariff-form").addEventListener("submit", (ev) => {
    if (ev.submitter && ev.submitter.value === "save") saveTariff();
  });
  $("battery-form").addEventListener("submit", saveBatteryConfig);

  await refreshStatus();
  await refreshLive();
  await refreshCharts();
  await Promise.all([refreshMoney(), refreshHistory(), refreshInsights(), refreshBatteryConfig()]);

  setInterval(refreshLive, 8000);
  setInterval(refreshCharts, 60000);
  setInterval(refreshStatus, 30000);
  setInterval(() => { refreshMoney(); refreshHistory(); refreshInsights(); }, 5 * 60000);
}

init();
