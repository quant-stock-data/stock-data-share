from __future__ import annotations

from .baostock_provider import BaoStockProvider
from .cninfo import CninfoProvider
from .eastmoney import EastmoneyProvider
from .nbs import NbsProvider
from .official import HKEXOfficialProvider, SSEOfficialProvider
from .sina import SinaProvider
from .tencent import TencentProvider


class AShareData:
    """Facade for non-tick A-share research data."""

    def __init__(self, eastmoney_min_interval: float = 2.0) -> None:
        self.tencent = TencentProvider()
        self.sina = SinaProvider()
        self.cninfo = CninfoProvider()
        self.eastmoney = EastmoneyProvider(min_interval=eastmoney_min_interval)
        self.baostock = BaoStockProvider()
        self.nbs = NbsProvider()
        self.sse = SSEOfficialProvider()
        self.hkex = HKEXOfficialProvider()

    def quote(self, symbol: str) -> dict:
        return self.tencent.quotes([symbol]).get(symbol, {})

    def daily_kline(self, symbol: str, **kwargs):
        return self.tencent.daily_kline(symbol, **kwargs)

    def minute_kline(self, symbol: str, **kwargs):
        return self.tencent.minute_kline(symbol, **kwargs)

    def financials(self, symbol: str, statement: str = "income", periods: int = 8):
        return self.sina.financial_statements(symbol, statement=statement, periods=periods)

    def announcements(self, symbol: str, page_size: int = 30):
        return self.cninfo.announcements(symbol, page_size=page_size)
