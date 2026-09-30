from __future__ import annotations

import json
import threading
from datetime import datetime, timedelta, timezone

import requests

from ..core.http import UA, make_session
from ..core.symbols import parse_symbol

CN_TZ = timezone(timedelta(hours=8))


class CninfoProvider:
    ORG_MAP_URL = "https://www.cninfo.com.cn/new/data/szse_stock.json"
    QUERY_URL = "https://www.cninfo.com.cn/new/hisAnnouncement/query"

    def __init__(self, session: requests.Session | None = None) -> None:
        self.session = session or make_session()
        self._org_map: dict[str, str] = {}
        self._lock = threading.Lock()

    @staticmethod
    def _json_utf8(response: requests.Response) -> dict:
        response.raise_for_status()
        return json.loads(response.content.decode("utf-8", errors="strict"))

    def _load_org_map(self) -> None:
        with self._lock:
            if self._org_map:
                return
            r = self.session.get(self.ORG_MAP_URL, headers={"User-Agent": UA}, timeout=20)
            data = self._json_utf8(r)
            self._org_map = {x["code"]: x["orgId"] for x in (data.get("stockList") or []) if x.get("code") and x.get("orgId")}

    def announcements(self, symbol: str, page_size: int = 30) -> list[dict]:
        sym = parse_symbol(symbol)
        self._load_org_map()
        org_id = self._org_map.get(sym.code)
        if not org_id:
            raise RuntimeError(f"CNINFO orgId not found for {sym.code}")
        payload = {
            "stock": f"{sym.code},{org_id}", "tabName": "fulltext",
            "pageSize": str(int(page_size)), "pageNum": "1", "column": "",
            "category": "", "plate": "", "seDate": "", "searchkey": "",
            "secid": "", "sortName": "", "sortType": "", "isHLtitle": "true",
        }
        headers = {
            "User-Agent": UA,
            "Content-Type": "application/x-www-form-urlencoded",
            "Referer": "https://www.cninfo.com.cn/new/disclosure",
            "Origin": "https://www.cninfo.com.cn",
        }
        r = self.session.post(self.QUERY_URL, data=payload, headers=headers, timeout=20)
        data = self._json_utf8(r)
        out = []
        for item in data.get("announcements") or []:
            ts = item.get("announcementTime")
            when = (
                datetime.fromtimestamp(ts / 1000, tz=CN_TZ).strftime("%Y-%m-%d")
                if isinstance(ts, (int, float))
                else str(ts or "")[:10]
            )
            attach = item.get("adjunctUrl") or ""
            out.append({
                "date": when,
                "title": item.get("announcementTitle", ""),
                "category": item.get("announcementTypeName", ""),
                "detail_url": f"https://www.cninfo.com.cn/new/disclosure/detail?annoId={item.get('announcementId', '')}",
                "download_url": f"https://static.cninfo.com.cn/{attach.lstrip('/')}" if attach else None,
                "source": "cninfo",
            })
        return out
