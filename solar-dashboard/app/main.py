"""NRG Command Center — FastAPI backend.

DEMO mode (no credentials): serves a deterministic simulation of Dave's
system so the full UI works end-to-end.
LIVE mode: polls the AlphaESS Open API on an interval, persists snapshots
and daily totals to SQLite, and proxies battery-config reads/writes.
"""

import asyncio
import logging
import os
from contextlib import asynccontextmanager
from datetime import date, datetime, timedelta
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from . import demo, store, tariff as tariff_mod
from .alphaess import AlphaESSClient, AlphaESSError, normalize_daily, normalize_live

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")

log = logging.getLogger("nrg")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

APP_ID = os.getenv("ALPHAESS_APP_ID", "").strip()
APP_SECRET = os.getenv("ALPHAESS_APP_SECRET", "").strip()
SYS_SN = os.getenv("ALPHAESS_SYS_SN", "").strip()
POLL_INTERVAL = max(15, int(os.getenv("POLL_INTERVAL", "30") or 30))
DEMO_MODE = (os.getenv("DEMO_MODE", "").strip().lower() in ("1", "true", "yes")
             or not (APP_ID and APP_SECRET))

client: AlphaESSClient | None = None
state = {"sn": SYS_SN or "AL7021025112659", "last_poll": None, "last_error": None}

DEFAULT_BATTERY_CONFIG = {
    "charge": {"gridCharge": 0, "batHighCap": 100.0,
               "timeChaf1": "00:00", "timeChae1": "00:00",
               "timeChaf2": "00:00", "timeChae2": "00:00"},
    "discharge": {"ctrDis": 0, "batUseCap": 10.0,
                  "timeDisf1": "00:00", "timeDise1": "00:00",
                  "timeDisf2": "00:00", "timeDise2": "00:00"},
}


def _ts_minute(dt: datetime) -> str:
    return dt.isoformat(timespec="minutes")


async def _poll_live_once():
    data = await client.get_last_power(state["sn"])
    snap = normalize_live(data)
    now = datetime.now()
    store.save_snapshot(_ts_minute(now), snap)
    state["last_poll"] = now.isoformat(timespec="seconds")
    state["last_error"] = None
    return snap


async def _refresh_daily(days_back: int = 14):
    today = date.today()
    for i in range(days_back + 1):
        d = today - timedelta(days=i)
        try:
            data = await client.get_one_date_energy(state["sn"], d.isoformat())
            if data:
                store.save_daily(d.isoformat(), normalize_daily(data))
            await asyncio.sleep(1.5)  # stay well inside API rate limits
        except AlphaESSError as e:
            log.warning("daily energy %s: %s", d, e)


async def _poller():
    if DEMO_MODE:
        return
    try:
        if not state["sn"]:
            systems = await client.get_ess_list() or []
            if systems:
                state["sn"] = systems[0].get("sysSn") or systems[0].get("sys_sn")
                log.info("using first bound system: %s", state["sn"])
        await _refresh_daily(14)
    except Exception as e:
        state["last_error"] = str(e)
        log.error("startup fetch failed: %s", e)

    last_daily = datetime.min
    while True:
        try:
            await _poll_live_once()
            if datetime.now() - last_daily > timedelta(hours=1):
                await _refresh_daily(1)
                last_daily = datetime.now()
        except Exception as e:
            state["last_error"] = str(e)
            log.error("poll failed: %s", e)
        await asyncio.sleep(POLL_INTERVAL)


@asynccontextmanager
async def lifespan(app: FastAPI):
    global client
    task = None
    if not DEMO_MODE:
        client = AlphaESSClient(APP_ID, APP_SECRET)
        task = asyncio.create_task(_poller())
    log.info("mode=%s sn=%s", "DEMO" if DEMO_MODE else "LIVE", state["sn"])
    yield
    if task:
        task.cancel()
    if client:
        await client.close()


app = FastAPI(title="NRG Command Center", lifespan=lifespan)


# ---------- API ----------

@app.get("/api/status")
async def status():
    return {
        "mode": "demo" if DEMO_MODE else "live",
        "sn": state["sn"],
        "battery_kwh": demo.BATTERY_KWH,
        "inverter_kw": demo.INVERTER_W / 1000,
        "last_poll": state["last_poll"],
        "last_error": state["last_error"],
        "poll_interval": POLL_INTERVAL,
        "server_time": datetime.now().isoformat(timespec="seconds"),
    }


@app.get("/api/live")
async def live():
    now = datetime.now()
    if DEMO_MODE:
        snap = demo.live_snapshot(now)
        store.save_snapshot(_ts_minute(now), snap)
        return {"ts": _ts_minute(now), **snap}
    rows = store.snapshots_for_day(now.date().isoformat())
    if rows:
        return rows[-1]
    raise HTTPException(503, "no live data yet — poller warming up")


@app.get("/api/today")
async def today():
    now = datetime.now()
    if DEMO_MODE:
        return demo.day_series(now.date(), until=now)
    rows = store.snapshots_for_day(now.date().isoformat())
    return rows


@app.get("/api/history")
async def history(days: int = 14):
    days = max(1, min(days, 60))
    today_d = date.today()
    t = store.get_setting("tariff", tariff_mod.DEFAULT_TARIFF)
    out = []
    for i in range(days - 1, -1, -1):
        d = today_d - timedelta(days=i)
        key = d.isoformat()
        if DEMO_MODE:
            e = demo.daily_energy(d, until=datetime.now())
            store.save_daily(key, e)
        else:
            found = store.daily_range([key])
            e = found[0] if found else None
        if e:
            e = {k: v for k, v in e.items() if k != "date"}
            out.append({"date": key, **e, "savings": tariff_mod.savings_from_daily(e, t)})
    return out


@app.get("/api/savings")
async def savings():
    t = store.get_setting("tariff", tariff_mod.DEFAULT_TARIFF)
    now = datetime.now()

    if DEMO_MODE:
        today_snaps = demo.day_series(now.date(), until=now)
    else:
        today_snaps = store.snapshots_for_day(now.date().isoformat())
    today_s = tariff_mod.savings_from_snapshots(today_snaps, t)

    hist = await history(days=7)
    week = round(sum(h["savings"]["saved"] for h in hist), 2)
    days_counted = max(1, len(hist))
    annual = round(week / days_counted * 365, 0)
    return {
        "today": today_s,
        "week_saved": week,
        "annual_projection": annual,
        "tariff": t,
    }


class TariffBody(BaseModel):
    mode: str = "flat"
    flat_import: float = 0.32
    feed_in: float = 0.05
    currency: str = "$"
    tou: list = []


@app.get("/api/tariff")
async def get_tariff():
    return store.get_setting("tariff", tariff_mod.DEFAULT_TARIFF)


@app.post("/api/tariff")
async def set_tariff(body: TariffBody):
    t = body.model_dump()
    if not t["tou"]:
        t["tou"] = tariff_mod.DEFAULT_TARIFF["tou"]
    store.set_setting("tariff", t)
    return t


@app.get("/api/battery-config")
async def battery_config():
    if DEMO_MODE:
        return store.get_setting("battery_config", DEFAULT_BATTERY_CONFIG)
    try:
        charge = await client.get_charge_config(state["sn"])
        discharge = await client.get_discharge_config(state["sn"])
        return {"charge": charge, "discharge": discharge}
    except AlphaESSError as e:
        raise HTTPException(502, str(e))


class BatteryConfigBody(BaseModel):
    charge: dict
    discharge: dict


@app.post("/api/battery-config")
async def set_battery_config(body: BatteryConfigBody):
    cfg = body.model_dump()
    if DEMO_MODE:
        store.set_setting("battery_config", cfg)
        return {"ok": True, "mode": "demo", "saved": cfg}
    c, d = cfg["charge"], cfg["discharge"]
    try:
        await client.update_charge_config(
            state["sn"], float(c["batHighCap"]), int(c["gridCharge"]),
            c["timeChaf1"], c["timeChae1"], c["timeChaf2"], c["timeChae2"],
        )
        await client.update_discharge_config(
            state["sn"], float(d["batUseCap"]), int(d["ctrDis"]),
            d["timeDisf1"], d["timeDise1"], d["timeDisf2"], d["timeDise2"],
        )
    except AlphaESSError as e:
        raise HTTPException(502, str(e))
    return {"ok": True, "mode": "live"}


@app.get("/api/insights")
async def insights():
    tips = []
    hist = await history(days=7)
    t = store.get_setting("tariff", tariff_mod.DEFAULT_TARIFF)
    cur = t.get("currency", "$")
    if hist:
        exports = sum(h["eoutput"] for h in hist)
        imports = sum(h["einput"] for h in hist)
        pv = sum(h["epv"] for h in hist)
        load = sum(h["eload"] for h in hist)
        if exports > 2 and imports > 2:
            fit = float(t.get("feed_in", 0.05))
            rate = float(t.get("flat_import", 0.32))
            tips.append({
                "level": "tip",
                "text": (f"Last 7 days you exported {exports:.1f} kWh at {cur}{fit:.2f} "
                         f"but imported {imports:.1f} kWh at {cur}{rate:.2f}. Every kWh "
                         f"shifted from export to later self-use is worth "
                         f"{cur}{rate - fit:.2f} — the battery schedule is the lever."),
            })
        if load > 0:
            self_sufficiency = max(0.0, 1 - imports / load) * 100
            tips.append({
                "level": "stat",
                "text": f"7-day self-sufficiency: {self_sufficiency:.0f}% of your "
                        f"home's energy came from your own solar + battery.",
            })
        if pv > 0 and exports / pv > 0.4:
            tips.append({
                "level": "warn",
                "text": (f"{exports / pv * 100:.0f}% of your generation was exported. "
                         "With a 20 kWh battery that suggests it fills early — worth "
                         "reviewing whether big loads (washing, EV) can run midday."),
            })
    if not tips:
        tips.append({"level": "stat", "text": "Collecting data — insights appear "
                                              "after a day or two of history."})
    return tips


# ---------- static frontend ----------

app.mount("/static", StaticFiles(directory=ROOT / "static"), name="static")


@app.get("/")
async def index():
    return FileResponse(ROOT / "static" / "index.html")
