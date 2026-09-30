from __future__ import annotations

import requests

from ..core.http import make_session
from ..core.symbols import parse_symbol


class SinaProvider:
    FINANCE_URL = "https://quotes.sina.cn/cn/api/openapi.php/CompanyFinanceService.getFinanceReport2022"

    def __init__(self, session: requests.Session | None = None) -> None:
        self.session = session or make_session()

    def financial_statements(self, symbol: str, statement: str = "income", periods: int = 8) -> list[dict]:
        mapping = {"balance": "fzb", "income": "lrb", "cashflow": "llb", "fzb": "fzb", "lrb": "lrb", "llb": "llb"}
        if statement not in mapping:
            raise ValueError("statement must be balance/income/cashflow")
        sym = parse_symbol(symbol)
        if sym.market == "bj":
            raise ValueError("Sina finance report endpoint is intended for Shanghai/Shenzhen stocks")
        params = {
            "paperCode": sym.tencent,
            "source": mapping[statement],
            "type": "0",
            "page": "1",
            "num": str(int(periods)),
        }
        r = self.session.get(self.FINANCE_URL, params=params, timeout=15)
        r.raise_for_status()
        payload = r.json() or {}
        report_list = ((((payload.get("result") or {}).get("data") or {}).get("report_list")) or {})
        out: list[dict] = []
        for period in sorted(report_list.keys(), reverse=True)[:periods]:
            record = {"period": f"{period[:4]}-{period[4:6]}-{period[6:8]}", "source": "sina"}
            for item in (report_list[period].get("data") or []):
                title = item.get("item_title")
                if not title:
                    continue
                record[title] = item.get("item_value")
                yoy = item.get("item_tongbi")
                if yoy not in (None, ""):
                    record[f"{title}_yoy"] = yoy
            out.append(record)
        return out
