from __future__ import annotations

import re
from urllib.parse import urljoin

import requests

from .http import make_session


class NbsProvider:
    INDEX_URL = "https://www.stats.gov.cn/sj/zxfb/"

    def __init__(self, session: requests.Session | None = None) -> None:
        self.session = session or make_session()

    def _text(self, url: str) -> str:
        r = self.session.get(url, timeout=30)
        r.raise_for_status()
        r.encoding = r.apparent_encoding or "utf-8"
        return r.text

    def pmi(self) -> dict:
        index = self._text(self.INDEX_URL)
        links = re.findall(r'<a[^>]+href="([^"]+)"[^>]*>\s*([^<]{6,100}?)\s*</a>', index)
        hit = next(((href, title) for href, title in links if "采购经理指数" in title), None)
        if not hit:
            raise RuntimeError("NBS latest releases page did not expose a PMI article")
        href, title = hit
        article_url = urljoin(self.INDEX_URL, href)
        html = self._text(article_url)
        text = re.sub(r"<(script|style)[^>]*>.*?</\1>", "", html, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r"<[^>]+>", "", text)
        text = re.sub(r"[\s\u3000\xa0]+", "", text)

        def grab(pattern: str) -> float | None:
            m = re.search(pattern, text)
            return float(m.group(1)) if m else None

        period = re.search(r"(\d{4})年(\d{1,2})月", title)
        out = {
            "period": f"{period.group(1)}-{int(period.group(2)):02d}" if period else None,
            "manufacturing_pmi": grab(r"(?<!非)制造业采购经理指数（PMI）为([\d.]+)%"),
            "non_manufacturing_pmi": grab(r"非制造业商务活动指数为([\d.]+)%"),
            "composite_pmi": grab(r"综合PMI产出指数为([\d.]+)%"),
            "title": re.sub(r"\s+", " ", title).strip(),
            "source": "nbs",
            "source_url": article_url,
        }
        missing = [k for k in ("manufacturing_pmi", "non_manufacturing_pmi", "composite_pmi") if out[k] is None]
        if missing:
            raise RuntimeError(f"NBS PMI article format changed; missing fields: {missing}")
        return out

