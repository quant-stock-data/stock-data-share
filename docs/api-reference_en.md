# API Reference

[中文](./api-reference.md) | [English](./api-reference_en.md)

## Entry point

~~~python
from ashare_data import AShareData

api = AShareData(eastmoney_min_interval=2.0)
~~~

## Market data

### `quote(symbol)`

~~~python
api.quote("600519")
~~~

Typical fields include price, previous close, open, change, high/low, turnover, PE, PB, market cap, and price limits.

### `daily_kline(symbol, start=None, end=None, limit=320, adjust="qfq")`

~~~python
api.daily_kline("600519", limit=100, adjust="qfq")
~~~

`adjust` accepts `qfq`, `hfq`, or `none`.

### `minute_kline(symbol, period="m5", limit=320)`

~~~python
api.minute_kline("600519", period="m15", limit=100)
~~~

`period` accepts `m1`, `m5`, `m15`, `m30`, or `m60`.

## Financials and disclosures

### `financials(symbol, statement="income", periods=8)`

~~~python
api.financials("600519", statement="balance", periods=8)
~~~

`statement` accepts `balance`, `income`, or `cashflow`.

### `announcements(symbol, page_size=30)`

~~~python
api.announcements("600519", page_size=20)
~~~

## Eastmoney provider

~~~python
em = api.eastmoney

em.stock_info("600519")
em.research_reports("600519", pages=1, page_size=20)
em.industry_reports(pages=1, page_size=20)
em.margin_trading("600519", limit=20)
em.block_trades("600519", limit=20)
em.holder_count("600519", limit=12)
em.dividends("600519", limit=20)
em.fund_flow_history("600519", limit=120)
~~~

## baostock provider

Install the optional dependency:

~~~bash
pip install -e ".[history]"
~~~

~~~python
api.baostock.stock_basic("600519")
api.baostock.valuation_history("600519", "2020-01-01", "2026-09-30")
~~~

## National Bureau of Statistics

~~~python
api.nbs.pmi()
~~~

## Shanghai Stock Exchange

~~~python
api.sse.etf_pcf("510180")
api.sse.regulatory_measures("600519", page_size=20)
~~~

## Hong Kong Exchanges and Clearing

~~~python
api.hkex.stock_connect_eligible("sse")
api.hkex.stock_connect_eligible("szse")
api.hkex.stock_connect_eligible("sse", sell_only=True)
~~~

## Error semantics

- Invalid parameters: usually `ValueError`
- Upstream schema changes or missing critical fields: usually `RuntimeError`
- HTTP failures: propagated through the corresponding `requests` exceptions

Callers should distinguish an upstream failure from a genuinely empty dataset.