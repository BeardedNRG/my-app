"""Demo-mode simulator shaped like Dave's system.

SMILE-M5 (5 kW hybrid inverter, output clipped at 5 kW), 20 kWh battery,
~10 kWp AlphaESS array mounted nearly flat, plus a legacy SMA Sunny Boy
(~2.7 kW, ~45° tilt) whose output the CT meter sees as reduced house load.
Winter southern-hemisphere sun (short day, low elevation).

Everything is deterministic per calendar date (seeded RNG), so history is
stable across restarts and the "live" tick is just today's profile read at
the current minute.
"""

import math
import random
from datetime import date, datetime, timedelta

BATTERY_KWH = 20.0
RESERVE_SOC = 10.0
MAX_SOC = 100.0
INVERTER_W = 5000.0

SUNRISE = 7.1   # ~07:05 winter
SUNSET = 17.4   # ~17:25


def _sun_factor(hour: float) -> float:
    """0..1 bell over daylight hours."""
    if hour <= SUNRISE or hour >= SUNSET:
        return 0.0
    x = (hour - SUNRISE) / (SUNSET - SUNRISE)
    return math.sin(math.pi * x) ** 1.4


def _day_profile(d: date) -> list:
    """Per-minute profile for one day: list of dicts with ppv/pload/pbat/pgrid/soc."""
    rng = random.Random(d.toordinal())
    # Day-level weather: 1.0 clear .. 0.35 overcast
    weather = rng.choice([1.0, 1.0, 0.9, 0.75, 0.9, 0.55, 1.0, 0.8, 0.35, 0.95])
    cloud_phase = rng.uniform(0, math.tau)
    cloud_speed = rng.uniform(2.5, 5.0)

    soc = rng.uniform(18, 42)  # start of day (post-overnight drain)
    out = []
    for m in range(0, 24 * 60):
        h = m / 60.0
        sun = _sun_factor(h)
        # passing clouds modulate minute to minute
        cloud = 1.0 - 0.35 * max(0.0, math.sin(cloud_phase + h * cloud_speed)) * (1.1 - weather)
        # 10 kWp flat array in winter tops out well under nameplate; clipped at 5 kW
        alpha_pv = min(INVERTER_W, 6800.0 * sun * weather * cloud)
        # Sunny Boy: 45° tilt catches low winter sun earlier/later, peaks ~2.4 kW
        sb_shift = _sun_factor(h + 0.0)
        legacy_pv = 2400.0 * (sb_shift ** 0.7) * weather * cloud

        # House load: baseline + morning & evening peaks
        base = 520.0
        morning = 1700.0 * math.exp(-((h - 7.3) ** 2) / 0.9)
        evening = 3300.0 * math.exp(-((h - 18.6) ** 2) / 2.4)  # winter heating
        midday = 500.0 * math.exp(-((h - 13.0) ** 2) / 6.0)
        noise = rng.uniform(-80, 220)
        gross_load = base + morning + evening + midday + max(0.0, noise)
        # CT meter sees load net of the legacy Sunny Boy
        load = max(120.0, gross_load - legacy_pv)

        ppv = alpha_pv
        surplus = ppv - load
        pbat = 0.0
        if surplus > 50 and soc < MAX_SOC:
            pbat = -min(surplus, INVERTER_W)          # charging (negative)
        elif surplus < -50 and soc > RESERVE_SOC:
            pbat = min(-surplus, INVERTER_W)          # discharging (positive)

        soc += (-pbat / 1000.0) / 60.0 / BATTERY_KWH * 100.0 * 0.96
        soc = max(RESERVE_SOC, min(MAX_SOC, soc))
        if soc in (RESERVE_SOC, MAX_SOC):
            # battery saturated: flow stops, grid takes the remainder
            pbat = 0.0 if abs(surplus) > 50 else pbat

        pgrid = load - ppv - pbat  # + import, - export
        out.append({
            "ppv": round(ppv, 1), "pload": round(load, 1),
            "pbat": round(pbat, 1), "pgrid": round(pgrid, 1),
            "soc": round(soc, 1),
        })
    return out


_profile_cache: dict = {}


def profile_for(d: date) -> list:
    key = d.isoformat()
    if key not in _profile_cache:
        if len(_profile_cache) > 40:
            _profile_cache.clear()
        _profile_cache[key] = _day_profile(d)
    return _profile_cache[key]


def live_snapshot(now: datetime) -> dict:
    prof = profile_for(now.date())
    return dict(prof[min(now.hour * 60 + now.minute, len(prof) - 1)])


def day_series(d: date, until: datetime | None = None, step_min: int = 5) -> list:
    """Snapshot series for a day at step_min resolution, timestamped."""
    prof = profile_for(d)
    limit = 24 * 60
    if until and until.date() == d:
        limit = until.hour * 60 + until.minute + 1
    rows = []
    for m in range(0, limit, step_min):
        ts = datetime(d.year, d.month, d.day) + timedelta(minutes=m)
        rows.append({"ts": ts.isoformat(timespec="minutes"), **prof[m]})
    return rows


def daily_energy(d: date, until: datetime | None = None) -> dict:
    """Integrate the day profile into kWh totals."""
    prof = profile_for(d)
    limit = 24 * 60
    if until and until.date() == d:
        limit = until.hour * 60 + until.minute + 1
    epv = eload = einput = eoutput = echarge = edischarge = 0.0
    for m in range(limit):
        p = prof[m]
        kwh = 1.0 / 60.0 / 1000.0
        epv += p["ppv"] * kwh
        eload += p["pload"] * kwh
        einput += max(0.0, p["pgrid"]) * kwh
        eoutput += max(0.0, -p["pgrid"]) * kwh
        echarge += max(0.0, -p["pbat"]) * kwh
        edischarge += max(0.0, p["pbat"]) * kwh
    return {
        "epv": round(epv, 2), "eload": round(eload, 2),
        "einput": round(einput, 2), "eoutput": round(eoutput, 2),
        "echarge": round(echarge, 2), "edischarge": round(edischarge, 2),
        "egridcharge": 0.0,
    }
