# ⚡ NRG Command Center

A self-hosted dashboard for Dave's AlphaESS solar + battery system
(SMILE-M5 5 kW hybrid inverter · 20 kWh battery · ~10 kWp array,
plus the legacy SMA Sunny Boy behind the CT meter).

Live power flow, battery state, history charts, savings estimates against
your electricity tariff, and a battery charge/discharge schedule panel that
talks to the real AlphaESS Open API.

## Quick start

```bash
cd solar-dashboard
python -m venv .venv
.venv\Scripts\activate        # Windows   (Linux/Mac: source .venv/bin/activate)
pip install -r requirements.txt
copy .env.example .env        # Windows   (Linux/Mac: cp .env.example .env)
python -m uvicorn app.main:app --port 8410
```

Open <http://localhost:8410>. With no credentials in `.env` it runs in
**DEMO mode** — a realistic simulation of this exact system (winter sun,
20 kWh battery physics) so the whole UI works out of the box.

## Going live

1. **Bind your system** at <https://open.alphaess.com> (the developer portal,
   not the AlphaCloud consumer app): add system with
   SN `AL7021025112659` + the **CheckCode** from the card / inverter label.
2. Put your `ALPHAESS_APP_ID` and `ALPHAESS_APP_SECRET` in `.env`.
3. Restart. The badge flips from DEMO to LIVE and the poller starts
   collecting real data every 30 s into `data/solar.db` (SQLite).

> History note: the app records live snapshots only while it's running.
> Daily kWh totals are backfilled from the AlphaESS cloud regardless.

## What's on the dashboard

| Panel | What it shows |
|---|---|
| Live power flow | A real-time **interactive 3D night scene** (three.js) — drag to orbit around the house. Glowing particle streams flow along the wires between roof array, battery cabinet, power pole and inverter; stream speed/size scales with watts, windows glow with house load, the battery LED shows charge direction. A `2D view` button swaps to a flat illustrated scene (or photo mode). |
| Stat tiles | Instant solar W, battery SOC, house draw, grid import/export |
| Today — power | 5-minute curves for all four channels |
| Battery charge | Today's SOC curve |
| Last 14 days | Daily kWh: generated, used, imported, exported |
| Money | Saved today / 7 days / annual pace vs. your tariff (edit via `rates ✎`) |
| Battery schedule | Reads & **writes** the AlphaESS charge/discharge config |
| Insights | Auto-generated observations (self-sufficiency, export vs import economics) |

### Photo mode — use a photo of YOUR house

The illustrated house can be swapped for a real photo with the data chips
and power lines drawn over it:

1. Save a wide (~16:9) photo of your house as `static/house.jpg`.
2. Copy `static/scene.example.json` to `static/scene.json`.
3. Tweak the chip positions / flow paths in that file (all coordinates are
   on an 800 × 460 grid over the image; instructions inside).

Delete `static/scene.json` to return to the illustration.

⚠️ **"Apply to system" is real in live mode** — it updates your inverter's
charge/discharge schedule via `updateChargeConfigInfo` /
`updateDisChargeConfigInfo`. In demo mode it only saves locally.

## Architecture

```
app/main.py      FastAPI server, background poller, REST API
app/alphaess.py  AlphaESS Open API client (SHA-512 signed headers)
app/demo.py      Deterministic system simulator (demo mode)
app/store.py     SQLite: snapshots, daily energy, settings
app/tariff.py    Tariff model + savings math (flat & time-of-use)
static/          Single-page frontend (vanilla JS + vendored Chart.js)
```

AlphaESS Open API reference:
<https://github.com/alphaess-developer/alphacloud_open_api>
