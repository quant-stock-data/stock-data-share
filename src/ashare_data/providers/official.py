from __future__ import annotations

import csv
import hashlib
import json
import re
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from io import StringIO
from typing import ClassVar

import requests

from ..core.http import UA, make_session
from ..core.symbols import parse_symbol


def _decode_text(response: requests.Response) -> str:
    """Decode exchange responses whose declared charset can be unreliable."""
    candidates = []
    for enc in (response.encoding, "utf-8", "gb18030"):
        if not enc:
            continue
        try:
            text = response.content.decode(enc, errors="replace")
        except LookupError:
            continue
        candidates.append(text)
    if not candidates:
        return response.content.decode("utf-8", errors="replace")
    return min(candidates, key=lambda s: s.count("\ufffd"))


def _json_or_jsonp(response: requests.Response) -> dict:
    text = _decode_text(response).strip()
    if text.startswith("{"):
        return json.loads(text)
    left, right = text.find("("), text.rfind(")")
    if left < 0 or right <= left:
        raise RuntimeError("unexpected JSONP response from official endpoint")
    return json.loads(text[left + 1:right])


class SSEOfficialProvider:
    """Official Shanghai Stock Exchange files/events, independent of quote vendors."""

    PCF_URL = "https://query.sse.com.cn/etfDownload/downloadETF2Bulletin.do"
    REG_URL = "https://query.sse.com.cn/commonSoaQuery.do"

    def __init__(self, session: requests.Session | None = None) -> None:
        self.session = session or make_session()

    def etf_pcf(self, fund_code: str) -> dict:
        """Download and normalize the official SSE ETF creation/redemption basket XML."""
        fund_code = str(fund_code).strip()
        if not re.fullmatch(r"\d{6}", fund_code):
            raise ValueError("fund_code must be a 6-digit SSE ETF code")
        headers = {"User-Agent": UA, "Referer": "https://www.sse.com.cn/disclosure/fund/etflist/"}
        r = self.session.get(self.PCF_URL, params={"fundCode": fund_code}, headers=headers, timeout=30)
        r.raise_for_status()
        raw = r.content
        root = ET.fromstring(raw)

        def text(tag: str) -> str | None:
            node = root.find(f".//{tag}")
            return node.text.strip() if node is not None and node.text else None

        component_list = root.find(".//ComponentList")
        components = []
        if component_list is not None:
            for node in list(component_list):
                item = {child.tag: (child.text or "").strip() for child in list(node)}
                if item:
                    components.append(item)
        record_number = int(text("RecordNumber") or 0)
        if record_number and record_number != len(components):
            raise RuntimeError(
                f"SSE PCF validation failed: RecordNumber={record_number}, components={len(components)}"
            )
        digest = hashlib.sha256(raw).hexdigest()
        return {
            "fund_code": text("FundInstrumentID") or fund_code,
            "trading_day": text("TradingDay"),
            "previous_trading_day": text("PreTradingDay"),
            "creation_redemption_unit": text("CreationRedemptionUnit"),
            "nav_per_cu": text("NAVperCU"),
            "nav": text("NAV"),
            "previous_cash_component": text("PreCashComponent"),
            "estimated_cash_component": text("EstimatedCashComponent"),
            "max_cash_ratio": text("MaxCashRatio"),
            "redemption_limit": text("RedemptionLimit"),
            "record_number": record_number,
            "components": components,
            "source": "sse",
            "source_url": r.url,
            "content_sha256": digest,
            "fetched_at": datetime.now(timezone.utc).isoformat(),
        }

    def regulatory_measures(
        self,
        symbol: str | None = None,
        *,
        start: str = "",
        end: str = "",
        page_size: int = 25,
    ) -> list[dict]:
        """Official SSE listed-company regulatory measures / disciplinary records."""
        stockcode = parse_symbol(symbol).code if symbol else ""
        if symbol and parse_symbol(symbol).market != "sh":
            raise ValueError("SSE regulatory endpoint only covers Shanghai-listed securities")
        params = {
            "jsonCallBack": "jsonpCallback", "isPagination": "true",
            "pageHelp.pageSize": str(min(max(int(page_size), 1), 100)), "pageHelp.pageNo": "1",
            "pageHelp.beginPage": "1", "pageHelp.cacheSize": "1", "pageHelp.endPage": "1",
            "sqlId": "BS_KCB_GGLL_NEW", "siteId": "28",
            "channelId": "10007,10008,10009,10010",
            "type": "", "stockcode": stockcode, "extTeacher": "", "extWTFL": "",
            "createTime": start, "createTimeEnd": end,
            "order": "createTime|desc,stockcode|asc",
        }
        headers = {"User-Agent": UA, "Referer": "https://www.sse.com.cn/regulation/supervision/measures/"}
        r = self.session.get(self.REG_URL, params=params, headers=headers, timeout=25)
        r.raise_for_status()
        data = _json_or_jsonp(r)
        rows = ((data.get("pageHelp") or {}).get("data") or [])
        out = []
        for x in rows:
            url = str(x.get("docURL") or "")
            if url and not url.startswith("http"):
                url = "https://" + url.lstrip("/")
            out.append({
                "code": x.get("stockcode") or x.get("extSECURITY_CODE"),
                "name": x.get("extGSJC"),
                "measure_type": x.get("extTYPE") or x.get("extWTFL"),
                "reason": x.get("docTitle"),
                "involved_party": x.get("extTeacher"),
                "date": str(x.get("createTime") or x.get("cmsOpDate") or "")[:10],
                "doc_id": x.get("docId"),
                "document_url": url or None,
                "source": "sse",
            })
        return out


class HKEXOfficialProvider:
    """Official Stock Connect eligibility files published by HKEX."""

    BASE = (
        "https://www.hkex.com.hk/-/media/HKEX-Market/Mutual-Market/Stock-Connect/"
        "Eligible-Stocks/View-All-Eligible-Securities/"
    )
    FILES: ClassVar[dict[tuple[str, bool], str]] = {
        ("sse", False): "SSE_Securities.csv",
        ("szse", False): "SZSE_Securities.csv",
        ("sse", True): "Special_SSE_Securities.csv",
        ("szse", True): "Special_SZSE_Securities.csv",
    }

    def __init__(self, session: requests.Session | None = None) -> None:
        self.session = session or make_session()

    def stock_connect_eligible(self, market: str = "sse", sell_only: bool = False) -> dict:
        key = (market.lower(), bool(sell_only))
        if key not in self.FILES:
            raise ValueError("market must be sse or szse")
        url = self.BASE + self.FILES[key]
        r = self.session.get(url, timeout=30)
        r.raise_for_status()
        raw = r.content
        text = raw.decode("utf-16")
        lines = [line.rstrip("\r\n") for line in text.splitlines()]
        updated = None
        for line in lines[:12]:
            m = re.search(r"Updated:\s*(.+)", line, flags=re.IGNORECASE)
            if m:
                updated = m.group(1).strip()
                break
        header_idx = next((i for i, line in enumerate(lines) if "Stock Code" in line and "Name" in line), None)
        if header_idx is None:
            raise RuntimeError("HKEX eligible file schema changed: header not found")
        reader = csv.DictReader(StringIO("\n".join(lines[header_idx:])), delimiter="\t")
        rows = []
        for row in reader:
            cleaned = {str(k).strip(): (v.strip() if isinstance(v, str) else v) for k, v in row.items() if k is not None}
            if any(cleaned.values()):
                rows.append(cleaned)
        return {
            "market": key[0], "sell_only": key[1], "updated": updated,
            "rows": rows, "row_count": len(rows),
            "source": "hkex", "source_url": r.url,
            "content_sha256": hashlib.sha256(raw).hexdigest(),
            "fetched_at": datetime.now(timezone.utc).isoformat(),
        }
