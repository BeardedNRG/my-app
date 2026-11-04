"""AlphaESS Open API client.

Auth per the official spec (github.com/alphaess-developer/alphacloud_open_api):
every request carries headers appId, timeStamp (unix seconds) and
sign = SHA512(appId + appSecret + timeStamp).
"""

import hashlib
import time

import httpx

BASE_URL = "https://openapi.alphaess.com/api"


class AlphaESSError(Exception):
    pass


class AlphaESSClient:
    def __init__(self, app_id: str, app_secret: str, timeout: float = 20.0):
        self.app_id = app_id
        self.app_secret = app_secret
        self._http = httpx.AsyncClient(base_url=BASE_URL, timeout=timeout)

    def _headers(self) -> dict:
        ts = str(int(time.time()))
        sign = hashlib.sha512(
            (self.app_id + self.app_secret + ts).encode("ascii")
        ).hexdigest()
        return {"appId": self.app_id, "timeStamp": ts, "sign": sign}

    async def _request(self, method: str, path: str, *, params=None, json=None):
        resp = await self._http.request(
            method, path, params=params, json=json, headers=self._headers()
        )
        resp.raise_for_status()
        body = resp.json()
        # Envelope: {"code": 200, "msg": "Success", "data": ...}
        if body.get("code") != 200:
            raise AlphaESSError(f"{path}: code={body.get('code')} msg={body.get('msg')}")
        return body.get("data")

    async def close(self):
        await self._http.aclose()

    # ---- systems ----
    async def get_ess_list(self):
        return await self._request("GET", "/getEssList")

    # ---- power / energy ----
    async def get_last_power(self, sys_sn: str):
        return await self._request("GET", "/getLastPowerData", params={"sysSn": sys_sn})

    async def get_one_day_power(self, sys_sn: str, query_date: str):
        return await self._request(
            "GET", "/getOneDayPowerBySn",
            params={"sysSn": sys_sn, "queryDate": query_date},
        )

    async def get_one_date_energy(self, sys_sn: str, query_date: str):
        return await self._request(
            "GET", "/getOneDateEnergyBySn",
            params={"sysSn": sys_sn, "queryDate": query_date},
        )

    # ---- battery charge (grid -> battery) config ----
    async def get_charge_config(self, sys_sn: str):
        return await self._request(
            "GET", "/getChargeConfigInfo", params={"sysSn": sys_sn}
        )

    async def update_charge_config(
        self, sys_sn: str, bat_high_cap: float, grid_charge: int,
        time_chaf1: str, time_chae1: str, time_chaf2: str, time_chae2: str,
    ):
        return await self._request(
            "POST", "/updateChargeConfigInfo",
            json={
                "sysSn": sys_sn,
                "batHighCap": bat_high_cap,
                "gridCharge": grid_charge,
                "timeChaf1": time_chaf1, "timeChae1": time_chae1,
                "timeChaf2": time_chaf2, "timeChae2": time_chae2,
            },
        )

    # ---- battery discharge config ----
    async def get_discharge_config(self, sys_sn: str):
        return await self._request(
            "GET", "/getDisChargeConfigInfo", params={"sysSn": sys_sn}
        )

    async def update_discharge_config(
        self, sys_sn: str, bat_use_cap: float, ctr_dis: int,
        time_disf1: str, time_dise1: str, time_disf2: str, time_dise2: str,
    ):
        return await self._request(
            "POST", "/updateDisChargeConfigInfo",
            json={
                "sysSn": sys_sn,
                "batUseCap": bat_use_cap,
                "ctrDis": ctr_dis,
                "timeDisf1": time_disf1, "timeDise1": time_dise1,
                "timeDisf2": time_disf2, "timeDise2": time_dise2,
            },
        )


def pick(d: dict, *candidates, default=None):
    """Case-insensitive field lookup — AlphaESS responses vary in key casing."""
    if not isinstance(d, dict):
        return default
    lower = {k.lower(): v for k, v in d.items()}
    for c in candidates:
        v = lower.get(c.lower())
        if v is not None:
            return v
    return default


def normalize_live(data: dict) -> dict:
    """Map getLastPowerData response to our snapshot shape (watts, %)."""
    return {
        "ppv": float(pick(data, "ppv", default=0) or 0),
        "pload": float(pick(data, "pload", "load", default=0) or 0),
        "pbat": float(pick(data, "pbat", default=0) or 0),   # + discharging, - charging
        "pgrid": float(pick(data, "pgrid", default=0) or 0), # + importing, - exporting
        "soc": float(pick(data, "soc", "cbat", default=0) or 0),
    }


def normalize_daily(data: dict) -> dict:
    """Map getOneDateEnergyBySn response to our daily-energy shape (kWh)."""
    return {
        "epv": float(pick(data, "epv", default=0) or 0),
        "eload": float(pick(data, "eload", "ehomeload", "eload1", default=0) or 0),
        "einput": float(pick(data, "einput", "egrid", default=0) or 0),    # grid import
        "eoutput": float(pick(data, "eoutput", "efeedin", default=0) or 0),  # feed-in
        "echarge": float(pick(data, "echarge", default=0) or 0),
        "edischarge": float(pick(data, "edischarge", default=0) or 0),
        "egridcharge": float(pick(data, "egridcharge", default=0) or 0),
    }
