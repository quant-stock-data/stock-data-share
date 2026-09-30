from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from ..core.http import UA, RateLimitedSession
from ..core.symbols import parse_symbol


class EastmoneyProvider:
    DATACENTER = "https://datacenter-web.eastmoney.com/api/data/v1/get"
    REPORT_API = "https://reportapi.eastmoney.com/report/list"
    REPORT_PDF = "https://pdf.dfcfw.com/pdf/H3_{info_code}_1.pdf"

    def __init__(self, min_interval: float = 2.0) -> None:
        self.http = RateLimitedSession(min_interval=min_interval)

    def stock_info(self, symbol: str) -> dict:
        sym = parse_symbol(symbol)
        url = "https://push2.eastmoney.com/api/qt/stock/get"
        params = {
            "fltt": "2", "invt": "2",
            "fields": "f57,f58,f84,f85,f127,f116,f117,f189,f43",
            "secid": sym.eastmoney_secid,
        }
        data = (self.http.get(url, params=params, timeout=15).json().get("data") or {})
        if not data:
            raise RuntimeError(f"Eastmoney returned no stock profile for {sym.code}")
        return {
            "code": data.get("f57"), "name": data.get("f58"), "industry": data.get("f127"),
            "total_shares": data.get("f84"), "float_shares": data.get("f85"),
            "market_cap": data.get("f116"), "float_market_cap": data.get("f117"),
            "list_date": str(data.get("f189") or ""), "price": data.get("f43"),
            "source": "eastmoney",
        }

    def research_reports(
        self,
        symbol: str,
        *,
        pages: int = 1,
        page_size: int = 50,
        years: int = 10,
    ) -> list[dict]:
        """Broker research reports for one stock, with a direct PDF URL when available."""
        code = parse_symbol(symbol).code
        now = datetime.now(timezone(timedelta(hours=8))).date()
        begin = (now - timedelta(days=365 * max(int(years), 1))).isoformat()
        out: list[dict] = []
        for page in range(1, max(int(pages), 1) + 1):
            params = {
                "industryCode": "*",
                "pageSize": str(min(max(int(page_size), 1), 100)),
                "industry": "*",
                "rating": "*",
                "ratingChange": "*",
                "beginTime": begin,
                "endTime": now.isoformat(),
                "pageNo": str(page),
                "fields": "",
                "qType": "0",
                "orgCode": "",
                "code": code,
                "rcode": "",
                "p": str(page),
                "pageNum": str(page),
                "pageNumber": str(page),
            }
            response = self.http.get(
                self.REPORT_API,
                params=params,
                headers={"Referer": "https://data.eastmoney.com/", "User-Agent": UA},
                timeout=30,
            )
            payload = response.json()
            rows = payload.get("data") or []
            for row in rows:
                info_code = row.get("infoCode")
                out.append(
                    {
                        "code": row.get("stockCode") or code,
                        "name": row.get("stockName"),
                        "date": str(row.get("publishDate") or "")[:10],
                        "title": row.get("title"),
                        "institution": row.get("orgSName"),
                        "rating": row.get("emRatingName"),
                        "industry": row.get("indvInduName"),
                        "eps_current_year": row.get("predictThisYearEps"),
                        "eps_next_year": row.get("predictNextYearEps"),
                        "eps_next_two_years": row.get("predictNextTwoYearEps"),
                        "pdf_url": self.REPORT_PDF.format(info_code=info_code) if info_code else None,
                        "info_code": info_code,
                        "source": "eastmoney",
                    }
                )
            total_pages = int(payload.get("TotalPage") or page)
            if not rows or page >= total_pages:
                break
        return out

    def industry_reports(
        self,
        industry_code: str = "*",
        *,
        pages: int = 1,
        page_size: int = 50,
        years: int = 2,
    ) -> list[dict]:
        """Industry research reports from the same report API, normalized separately."""
        now = datetime.now(timezone(timedelta(hours=8))).date()
        begin = (now - timedelta(days=365 * max(int(years), 1))).isoformat()
        out: list[dict] = []
        for page in range(1, max(int(pages), 1) + 1):
            params = {
                "industryCode": industry_code,
                "pageSize": str(min(max(int(page_size), 1), 100)),
                "industry": "*",
                "rating": "*",
                "ratingChange": "*",
                "beginTime": begin,
                "endTime": now.isoformat(),
                "pageNo": str(page),
                "fields": "",
                "qType": "1",
                "orgCode": "",
                "code": "*",
                "rcode": "",
                "p": str(page),
                "pageNum": str(page),
                "pageNumber": str(page),
            }
            payload = self.http.get(
                self.REPORT_API,
                params=params,
                headers={"Referer": "https://data.eastmoney.com/", "User-Agent": UA},
                timeout=30,
            ).json()
            rows = payload.get("data") or []
            for row in rows:
                info_code = row.get("infoCode")
                out.append(
                    {
                        "date": str(row.get("publishDate") or "")[:10],
                        "title": row.get("title"),
                        "institution": row.get("orgSName"),
                        "industry_code": row.get("industryCode"),
                        "industry": row.get("industryName"),
                        "rating": row.get("emRatingName"),
                        "pdf_url": self.REPORT_PDF.format(info_code=info_code) if info_code else None,
                        "info_code": info_code,
                        "source": "eastmoney",
                    }
                )
            total_pages = int(payload.get("TotalPage") or page)
            if not rows or page >= total_pages:
                break
        return out

    def _datacenter(
        self,
        report_name: str,
        *,
        filter_text: str = "",
        columns: str = "ALL",
        sort_columns: str = "",
        sort_types: str = "-1",
        page_size: int = 50,
        max_pages: int = 3,
    ) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        for page in range(1, max_pages + 1):
            params = {
                "reportName": report_name, "columns": columns, "filter": filter_text,
                "pageNumber": str(page), "pageSize": str(page_size),
                "sortColumns": sort_columns, "sortTypes": sort_types,
                "source": "WEB", "client": "WEB",
            }
            payload = self.http.get(self.DATACENTER, params=params, headers={"User-Agent": UA}, timeout=20).json()
            result = payload.get("result")
            if result is None:
                raise RuntimeError(f"Eastmoney datacenter failed for {report_name}: {payload.get('message') or payload}")
            page_rows = result.get("data") or []
            rows.extend(page_rows)
            total_pages = int(result.get("pages") or page)
            if not page_rows or page >= total_pages:
                break
        return rows

    def margin_trading(self, symbol: str, limit: int = 30) -> list[dict]:
        code = parse_symbol(symbol).code
        rows = self._datacenter(
            "RPTA_WEB_RZRQ_GGMX", filter_text=f'(SCODE="{code}")',
            sort_columns="DATE", sort_types="-1", page_size=min(max(limit, 1), 100), max_pages=1,
        )
        return [{
            "date": str(x.get("DATE") or "")[:10], "financing_balance": x.get("RZYE"),
            "financing_buy": x.get("RZMRE"), "financing_repay": x.get("RZCHE"),
            "short_balance": x.get("RQYE"), "short_sell_volume": x.get("RQMCL"),
            "short_repay_volume": x.get("RQCHL"), "total_margin_balance": x.get("RZRQYE"),
            "source": "eastmoney",
        } for x in rows[:limit]]

    def block_trades(self, symbol: str, limit: int = 20) -> list[dict]:
        code = parse_symbol(symbol).code
        rows = self._datacenter(
            "RPT_DATA_BLOCKTRADE", filter_text=f'(SECURITY_CODE="{code}")',
            sort_columns="TRADE_DATE", sort_types="-1", page_size=min(max(limit, 1), 100), max_pages=1,
        )
        out = []
        for x in rows[:limit]:
            close = float(x.get("CLOSE_PRICE") or 0)
            price = float(x.get("DEAL_PRICE") or 0)
            out.append({
                "date": str(x.get("TRADE_DATE") or "")[:10], "price": price, "close": close,
                "premium_pct": round((price / close - 1) * 100, 3) if close else None,
                "volume": x.get("DEAL_VOLUME"), "amount": x.get("DEAL_AMT"),
                "buyer": x.get("BUYER_NAME"), "seller": x.get("SELLER_NAME"), "source": "eastmoney",
            })
        return out

    def holder_count(self, symbol: str, limit: int = 12) -> list[dict]:
        code = parse_symbol(symbol).code
        rows = self._datacenter(
            "RPT_HOLDERNUMLATEST", filter_text=f'(SECURITY_CODE="{code}")',
            sort_columns="END_DATE", sort_types="-1", page_size=min(max(limit, 1), 100), max_pages=1,
        )
        return [{
            "date": str(x.get("END_DATE") or "")[:10], "holders": x.get("HOLDER_NUM"),
            "holder_change": x.get("HOLDER_NUM_CHANGE"), "holder_change_pct": x.get("HOLDER_NUM_RATIO"),
            "avg_free_shares": x.get("AVG_FREE_SHARES"), "source": "eastmoney",
        } for x in rows[:limit]]

    def dividends(self, symbol: str, limit: int = 20) -> list[dict]:
        code = parse_symbol(symbol).code
        rows = self._datacenter(
            "RPT_SHAREBONUS_DET", filter_text=f'(SECURITY_CODE="{code}")',
            sort_columns="EX_DIVIDEND_DATE", sort_types="-1", page_size=min(max(limit, 1), 100), max_pages=1,
        )
        return [{
            "date": str(x.get("EX_DIVIDEND_DATE") or "")[:10], "cash_per_share": x.get("PRETAX_BONUS_RMB"),
            "transfer_per_10": x.get("TRANSFER_RATIO"), "bonus_per_10": x.get("BONUS_RATIO"),
            "status": x.get("ASSIGN_PROGRESS"), "source": "eastmoney",
        } for x in rows[:limit]]

    def fund_flow_history(self, symbol: str, limit: int = 120) -> list[dict]:
        sym = parse_symbol(symbol)
        url = "https://push2his.eastmoney.com/api/qt/stock/fflow/daykline/get"
        params = {
            "secid": sym.eastmoney_secid,
            "fields1": "f1,f2,f3,f7",
            "fields2": "f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61,f62,f63,f64,f65",
            "lmt": str(int(limit)),
        }
        headers = {"User-Agent": UA, "Referer": "https://quote.eastmoney.com/", "Origin": "https://quote.eastmoney.com"}
        data = self.http.get(url, params=params, headers=headers, timeout=20).json().get("data") or {}
        rows = data.get("klines") or []
        out = []
        for line in rows:
            x = line.split(",")
            if len(x) < 6:
                continue
            def number(v: str) -> float | None:
                try: return float(v) if v != "-" else None
                except ValueError: return None
            out.append({
                "date": x[0], "main_net": number(x[1]), "small_net": number(x[2]),
                "medium_net": number(x[3]), "large_net": number(x[4]), "super_net": number(x[5]),
                "source": "eastmoney",
            })
        return out
