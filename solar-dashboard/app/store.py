"""SQLite persistence: live snapshots, daily energy totals, settings."""

import json
import sqlite3
import threading
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "solar.db"

_lock = threading.Lock()
_conn: sqlite3.Connection | None = None


def _connect() -> sqlite3.Connection:
    global _conn
    if _conn is None:
        DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        _conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        _conn.row_factory = sqlite3.Row
        _conn.executescript("""
            CREATE TABLE IF NOT EXISTS snapshots (
                ts TEXT PRIMARY KEY,          -- ISO minute resolution, local time
                ppv REAL, pload REAL, pbat REAL, pgrid REAL, soc REAL
            );
            CREATE TABLE IF NOT EXISTS daily_energy (
                date TEXT PRIMARY KEY,        -- YYYY-MM-DD
                epv REAL, eload REAL, einput REAL, eoutput REAL,
                echarge REAL, edischarge REAL, egridcharge REAL
            );
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY, value TEXT
            );
        """)
    return _conn


def save_snapshot(ts: str, snap: dict):
    with _lock:
        c = _connect()
        c.execute(
            "INSERT OR REPLACE INTO snapshots (ts, ppv, pload, pbat, pgrid, soc) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (ts, snap["ppv"], snap["pload"], snap["pbat"], snap["pgrid"], snap["soc"]),
        )
        c.commit()


def snapshots_for_day(day: str) -> list:
    with _lock:
        rows = _connect().execute(
            "SELECT * FROM snapshots WHERE ts LIKE ? ORDER BY ts", (day + "%",)
        ).fetchall()
    return [dict(r) for r in rows]


def save_daily(day: str, e: dict):
    with _lock:
        c = _connect()
        c.execute(
            "INSERT OR REPLACE INTO daily_energy "
            "(date, epv, eload, einput, eoutput, echarge, edischarge, egridcharge) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (day, e["epv"], e["eload"], e["einput"], e["eoutput"],
             e["echarge"], e["edischarge"], e.get("egridcharge", 0.0)),
        )
        c.commit()


def daily_range(days: list) -> list:
    qmarks = ",".join("?" * len(days))
    with _lock:
        rows = _connect().execute(
            f"SELECT * FROM daily_energy WHERE date IN ({qmarks}) ORDER BY date",
            days,
        ).fetchall()
    return [dict(r) for r in rows]


def get_setting(key: str, default=None):
    with _lock:
        row = _connect().execute(
            "SELECT value FROM settings WHERE key = ?", (key,)
        ).fetchone()
    return json.loads(row["value"]) if row else default


def set_setting(key: str, value):
    with _lock:
        c = _connect()
        c.execute(
            "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
            (key, json.dumps(value)),
        )
        c.commit()
