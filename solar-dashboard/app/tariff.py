"""Tariff model + savings math.

Savings = what the grid would have billed with no solar/battery
          minus what it actually bills now (imports at tariff, exports at FiT).
Time-of-use is supported by bucketing each snapshot into the window whose
rate applies at that minute.
"""

from datetime import datetime

DEFAULT_TARIFF = {
    "mode": "flat",              # "flat" | "tou"
    "flat_import": 0.32,         # $/kWh
    "feed_in": 0.05,             # $/kWh
    "currency": "$",
    "tou": [                     # used when mode == "tou"; first match wins
        {"name": "Peak",     "start": "16:00", "end": "21:00", "rate": 0.45},
        {"name": "Off-peak", "start": "22:00", "end": "07:00", "rate": 0.22},
        {"name": "Shoulder", "start": "00:00", "end": "24:00", "rate": 0.30},
    ],
}


def _minutes(hhmm: str) -> int:
    h, m = hhmm.split(":")
    return int(h) * 60 + int(m)


def rate_at(tariff: dict, ts: datetime) -> float:
    if tariff.get("mode") != "tou":
        return float(tariff.get("flat_import", 0.32))
    t = ts.hour * 60 + ts.minute
    for w in tariff.get("tou", []):
        start, end = _minutes(w["start"]), _minutes(w["end"])
        if start <= end:
            if start <= t < end:
                return float(w["rate"])
        else:  # window wraps midnight
            if t >= start or t < end:
                return float(w["rate"])
    return float(tariff.get("flat_import", 0.32))


def savings_from_snapshots(snapshots: list, tariff: dict) -> dict:
    """Integrate a snapshot series (assumed evenly spaced) into $ figures."""
    if len(snapshots) < 2:
        return {"baseline": 0.0, "actual": 0.0, "saved": 0.0, "export_earned": 0.0}
    t0 = datetime.fromisoformat(snapshots[0]["ts"])
    t1 = datetime.fromisoformat(snapshots[1]["ts"])
    dt_h = max((t1 - t0).total_seconds(), 60) / 3600.0

    baseline = actual_import = export_earned = 0.0
    fit = float(tariff.get("feed_in", 0.0))
    for s in snapshots:
        ts = datetime.fromisoformat(s["ts"])
        r = rate_at(tariff, ts)
        kwh = dt_h / 1000.0
        baseline += s["pload"] * kwh * r
        actual_import += max(0.0, s["pgrid"]) * kwh * r
        export_earned += max(0.0, -s["pgrid"]) * kwh * fit
    actual = actual_import - export_earned
    return {
        "baseline": round(baseline, 2),
        "actual": round(actual, 2),
        "saved": round(baseline - actual, 2),
        "export_earned": round(export_earned, 2),
        "import_cost": round(actual_import, 2),
    }


def savings_from_daily(day: dict, tariff: dict) -> dict:
    """Coarse daily savings from kWh totals (flat-rate approximation for TOU)."""
    # blended import rate: flat rate, or time-weighted average of TOU windows
    if tariff.get("mode") == "tou":
        total, weighted = 0, 0.0
        for w in tariff.get("tou", []):
            start, end = _minutes(w["start"]), _minutes(w["end"])
            span = (end - start) if end >= start else (24 * 60 - start + end)
            weighted += span * float(w["rate"])
            total += span
        rate = weighted / total if total else float(tariff.get("flat_import", 0.32))
    else:
        rate = float(tariff.get("flat_import", 0.32))
    fit = float(tariff.get("feed_in", 0.0))

    baseline = day["eload"] * rate
    actual = day["einput"] * rate - day["eoutput"] * fit
    return {
        "baseline": round(baseline, 2),
        "actual": round(actual, 2),
        "saved": round(baseline - actual, 2),
        "export_earned": round(day["eoutput"] * fit, 2),
    }
