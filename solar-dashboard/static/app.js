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

/* ---------- power flow SVG ---------- */

const NS = "http://www.w3.org/2000/svg";
const flowEls = {};

function el(name, attrs, parent) {
  const e = document.createElementNS(NS, name);
  for (const [k, v] of Object.entries(attrs)) e.setAttribute(k, v);
  parent.appendChild(e);
  return e;
}

function buildFlow() {
  const svg = $("flow");
  const nodes = {
    solar:   { x: 250, y: 14,  w: 148, h: 66, label: "Solar",   icon: "☀" },
    battery: { x: 16,  y: 138, w: 158, h: 66, label: "Battery", icon: "🔋" },
    home:    { x: 466, y: 138, w: 158, h: 66, label: "Home",    icon: "⌂" },
    grid:    { x: 250, y: 262, w: 148, h: 66, label: "Grid",    icon: "⚡" },
  };
  const wires = {
    solar:   "M 324 80 L 324 144",
    battery: "M 174 171 L 296 171",
    home:    "M 352 171 L 466 171",
    grid:    "M 324 262 L 324 198",
  };
  // static wires underneath
  for (const d of Object.values(wires)) el("path", { d, class: "wire" }, svg);
  // animated flow lines
  for (const [k, d] of Object.entries(wires)) {
    flowEls[k] = el("path", { d, class: "flowline", stroke: COLORS[k === "grid" ? "grid" : k] }, svg);
  }
  // hub
  el("circle", { cx: 324, cy: 171, r: 27, class: "hub" }, svg);
  el("circle", { cx: 324, cy: 171, r: 27, class: "hub-pulse" }, svg);
  el("circle", { cx: 324, cy: 171, r: 7, class: "hub-core" }, svg);
  const hubTxt = el("text", { x: 324, y: 214, "text-anchor": "middle", class: "node-sub" }, svg);
  hubTxt.textContent = "SMILE-M5 · 5 kW";

  for (const [k, n] of Object.entries(nodes)) {
    el("rect", { x: n.x, y: n.y, width: n.w, height: n.h, rx: 12, class: "node-box" }, svg);
    const t1 = el("text", { x: n.x + 14, y: n.y + 22, class: "node-label" }, svg);
    t1.textContent = `${n.icon} ${n.label}`;
    flowEls[k + "Val"] = el("text", { x: n.x + 14, y: n.y + 45, class: "node-value" }, svg);
    flowEls[k + "Sub"] = el("text", { x: n.x + 14, y: n.y + 59, class: "node-sub" }, svg);
  }
}

function setFlow(line, watts, reverse) {
  const on = Math.abs(watts) > 40;
  line.classList.toggle("on", on);
  line.classList.toggle("rev", !!reverse);
  line.style.strokeWidth = (2 + Math.min(3.5, Math.abs(watts) / 1400)).toFixed(1);
  line.style.animationDuration = `${Math.max(0.35, 1.4 - Math.abs(watts) / 5000)}s`;
}

function updateFlow(s) {
  flowEls.solarVal.textContent = fmtKw(s.ppv);
  flowEls.solarSub.textContent = s.ppv > 20 ? "generating" : "asleep";
  flowEls.batteryVal.textContent = `${s.soc.toFixed(0)} %`;
  flowEls.batterySub.textContent =
    s.pbat < -40 ? `charging ${fmtKw(-s.pbat)}` :
    s.pbat > 40 ? `discharging ${fmtKw(s.pbat)}` : "idle";
  flowEls.homeVal.textContent = fmtKw(s.pload);
  flowEls.homeSub.textContent = "house load";
  flowEls.gridVal.textContent = fmtKw(Math.abs(s.pgrid));
  flowEls.gridSub.textContent =
    s.pgrid > 40 ? "importing" : s.pgrid < -40 ? "exporting" : "balanced";

  setFlow(flowEls.solar, s.ppv, false);                    // solar → hub
  setFlow(flowEls.battery, s.pbat, s.pbat < 0);            // hub ↔ battery
  setFlow(flowEls.home, s.pload, false);                   // hub → home
  setFlow(flowEls.grid, s.pgrid, s.pgrid < 0);             // grid ↔ hub
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
  buildFlow();
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
