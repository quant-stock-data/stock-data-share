from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager

import pandas as pd

from ..core.symbols import parse_symbol


def _bs():
    try:
        import baostock as bs
    except ImportError as exc:
        raise RuntimeError("baostock is optional; install with: pip install 'stock-data-share[history]'") from exc
    return bs


@contextmanager
def _session() -> Iterator[object]:
    bs = _bs()
    login = bs.login()
    if login.error_code != "0":
        raise RuntimeError(f"baostock login failed: {login.error_code} {login.error_msg}")
    try:
        yield bs
    finally:
        bs.logout()


def _to_df(result) -> pd.DataFrame:
    if result.error_code != "0":
        raise RuntimeError(f"baostock query failed: {result.error_code} {result.error_msg}")
    rows = []
    while result.next():
        rows.append(result.get_row_data())
    return pd.DataFrame(rows, columns=result.fields)


class BaoStockProvider:
    def valuation_history(self, symbol: str, start: str, end: str) -> pd.DataFrame:
        sym = parse_symbol(symbol)
        bs_code = sym.baostock
        fields = "date,code,close,peTTM,pbMRQ,psTTM,pcfNcfTTM,turn,tradestatus,isST"
        with _session() as bs:
            df = _to_df(bs.query_history_k_data_plus(
                bs_code, fields, start_date=start, end_date=end, frequency="d", adjustflag="3"
            ))
        for col in ("close", "peTTM", "pbMRQ", "psTTM", "pcfNcfTTM", "turn"):
            if col in df:
                df[col] = pd.to_numeric(df[col], errors="coerce")
        return df

    def stock_basic(self, symbol: str) -> dict:
        sym = parse_symbol(symbol)
        with _session() as bs:
            df = _to_df(bs.query_stock_basic(code=sym.baostock))
        return df.iloc[0].to_dict() if not df.empty else {}
