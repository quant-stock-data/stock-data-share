---
name: stock-data-share
description: Route A-share research and market-data requests to the appropriate stock-data-share Python API and public source.
---

# stock-data-share Agent Guide

This file is a compact routing guide for AI coding agents and research assistants using this repository.

## Entry point

~~~python
from ashare_data import AShareData
api = AShareData()
~~~

## Routing table

| Intent | Python call | Primary source |
|---|---|---|
| Latest stock snapshot | `api.quote(symbol)` | Tencent |
| Daily K-line | `api.daily_kline(symbol, ...)` | Tencent |
| Minute K-line | `api.minute_kline(symbol, ...)` | Tencent |
| Financial statements | `api.financials(symbol, ...)` | Sina |
| Announcements | `api.announcements(symbol, ...)` | CNINFO |
| Company profile | `api.eastmoney.stock_info(symbol)` | Eastmoney |
| Stock research reports | `api.eastmoney.research_reports(symbol, ...)` | Eastmoney |
| Industry research reports | `api.eastmoney.industry_reports(...)` | Eastmoney |
| Margin trading | `api.eastmoney.margin_trading(symbol, ...)` | Eastmoney |
| Block trades | `api.eastmoney.block_trades(symbol, ...)` | Eastmoney |
| Shareholder count | `api.eastmoney.holder_count(symbol, ...)` | Eastmoney |
| Dividends | `api.eastmoney.dividends(symbol, ...)` | Eastmoney |
| Fund-flow history | `api.eastmoney.fund_flow_history(symbol, ...)` | Eastmoney |
| Historical valuation | `api.baostock.valuation_history(symbol, start, end)` | baostock |
| Stock listing basics | `api.baostock.stock_basic(symbol)` | baostock |
| Latest PMI | `api.nbs.pmi()` | NBS |
| SSE ETF PCF | `api.sse.etf_pcf(fund_code)` | SSE |
| SSE regulatory measures | `api.sse.regulatory_measures(...)` | SSE |
| Stock Connect eligibility | `api.hkex.stock_connect_eligible(...)` | HKEX |

## Symbol normalization

Accepted formats include:

~~~text
600519
sh600519
600519.SH
bj920982
~~~

Use explicit market prefixes when the numeric code is ambiguous.

## Source-selection rules

1. Prefer the facade methods for common quote, K-line, financial, and announcement tasks.
2. Use provider-specific methods when the request clearly maps to one specialized dataset.
3. Preserve `source` and `source_url` fields in downstream results when available.
4. Treat an upstream exception as a source failure, not as proof that the requested data does not exist.
5. Do not invent fields that are not present in the provider response.
6. For historical valuation, ensure the optional `history` dependency is installed.
7. For official-file datasets, retain `fetched_at` and `content_sha256` when returned.

## Common workflows

### Single-stock research

Recommended sequence:

1. `quote`
2. `daily_kline`
3. `financials`
4. `eastmoney.stock_info`
5. `eastmoney.research_reports`
6. `announcements`
7. optional capital-data endpoints

### Event research

Use the official providers first when the question concerns exchange-published events:

- SSE regulatory actions → `api.sse.regulatory_measures`
- ETF basket / creation-redemption file → `api.sse.etf_pcf`
- Stock Connect eligibility → `api.hkex.stock_connect_eligible`

### Historical valuation

~~~python
df = api.baostock.valuation_history(
    "600519",
    "2020-01-01",
    "2026-09-30",
)
~~~

The result is a pandas DataFrame.

## Verification

Before claiming a provider is working in the current environment:

~~~bash
pytest -q
ruff check src tests
python tests/smoke_live.py
~~~

Unit tests validate local logic. The live smoke suite validates current external-source reachability.