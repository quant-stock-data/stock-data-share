from __future__ import annotations

from collections.abc import Iterable
from datetime import datetime, timedelta, timezone

import requests

from .http import UA, make_session
from .symbols import parse_symbol

CN_TZ = timezone(timedelta(hours=8))


def _f(value: str | None) -> float | None:
    if value in (None, "", "-"):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


class TencentProvider:
    QUOTE_URL = "https://qt.gtimg.cn/q="
    DAILY_URL = "https://web.ifzq.gtimg.cn/appstock/app/fqkline/get"
    MINUTE_URL = "https://ifzq.gtimg.cn/appstock/app/kline/mkline"

    def __init__(self, session: requests.Session | None = None) -> None:
        self.session = session or make_session()

    def quotes(self, symbols: Iterable[str]) -> dict[str, dict]:
        parsed = [(raw, parse_symbol(raw)) for raw in symbols]
        query = ",".join(s.tencent for _, s in parsed)
        r = self.session.get(self.QUOTE_URL + query, timeout=15)
        r.raise_for_status()
        text = r.content.decode("gbk", errors="replace")
        by_key = {s.tencent: raw for raw, s in parsed}
        out: dict[str, dict] = {}
        for line in text.split(";"):
            if "=" not in line or '"' not in line:
                continue
            wire_key = line.split("=", 1)[0].rsplit("_", 1)[-1]
            fields = line.split('"', 2)[1].split("~")
            if len(fields) < 53:
                continue
            raw_key = by_key.get(wire_key, wire_key)
            out[raw_key] = {
                "code": fields[2],
                "name": fields[1],
                "price": _f(fields[3]),
                "previous_close": _f(fields[4]),
                "open": _f(fields[5]),
                "change": _f(fields[31]),
                "change_pct": _f(fields[32]),
                "high": _f(fields[33]),
                "low": _f(fields[34]),
                "amount_10k": _f(fields[37]),
                "turnover_pct": _f(fields[38]),
                "pe_ttm": _f(fields[39]),
                "amplitude_pct": _f(fields[43]),
                "float_market_cap_100m": _f(fields[44]),
                "market_cap_100m": _f(fields[45]),
                "pb": _f(fields[46]),
                "limit_up": _f(fields[47]),
                "limit_down": _f(fields[48]),
                "volume_ratio": _f(fields[49]),
                "pe_static": _f(fields[52]),
                "source": "tencent",
                "source_url": self.QUOTE_URL + wire_key,
            }
        return out

    def daily_kline(
        self,
        symbol: str,
        start: str | None = None,
        end: str | None = None,
        limit: int = 320,
        adjust: str = "qfq",
    ) -> list[dict]:
        sym = parse_symbol(symbol)
        if sym.market == "bj":
            raise ValueError("Tencent K-line endpoint does not reliably cover Beijing Stock Exchange")
        if adjust not in {"qfq", "hfq", "none"}:
            raise ValueError("adjust must be qfq, hfq, or none")
        today = datetime.now(CN_TZ).date()
        end = end or today.isoformat()
        start = start or (today - timedelta(days=550)).isoformat()
        adj = "" if adjust == "none" else adjust
        params = {"param": f"{sym.tencent},day,{start},{end},{int(limit)},{adj}"}
        r = self.session.get(self.DAILY_URL, params=params, headers={"Referer": "https://gu.qq.com/", "User-Agent": UA}, timeout=15)
        r.raise_for_status()
        node = ((r.json().get("data") or {}).get(sym.tencent) or {})
        key = "day" if adjust == "none" else f"{adjust}day"
        rows = node.get(key) or []
        return [
            {
                "date": x[0], "open": _f(x[1]), "close": _f(x[2]),
                "high": _f(x[3]), "low": _f(x[4]), "volume": _f(x[5]),
                "adjust": adjust, "source": "tencent",
            }
            for x in rows if len(x) >= 6
        ]

    def minute_kline(self, symbol: str, period: str = "m5", limit: int = 320) -> list[dict]:
        sym = parse_symbol(symbol)
        if sym.market == "bj":
            raise ValueError("Tencent minute K-line does not reliably cover Beijing Stock Exchange")
        if period not in {"m1", "m5", "m15", "m30", "m60"}:
            raise ValueError("period must be one of m1/m5/m15/m30/m60")
        params = {"param": f"{sym.tencent},{period},,{int(limit)}"}
        r = self.session.get(self.MINUTE_URL, params=params, headers={"Referer": "https://gu.qq.com/", "User-Agent": UA}, timeout=15)
        r.raise_for_status()
        node = ((r.json().get("data") or {}).get(sym.tencent) or {})
        rows = node.get(period) or []
        return [
            {
                "time": x[0], "open": _f(x[1]), "close": _f(x[2]),
                "high": _f(x[3]), "low": _f(x[4]), "volume": _f(x[5]),
                "period": period, "source": "tencent",
            }
            for x in rows if len(x) >= 6
        ]
