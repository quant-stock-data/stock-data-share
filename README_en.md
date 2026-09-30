<p align="center"><a href="./README.md">简体中文</a> · <b>English</b></p>

<h1 align="center">stock-data-share</h1>

<p align="center"><b>China A-share research & quantitative data toolkit · multi-source routing · official datasets · traceable results</b></p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/version-0.1.0-2ea44f" alt="Version">
  <img src="https://img.shields.io/badge/license-Apache--2.0-blue" alt="License">
  <img src="https://img.shields.io/badge/sources-8-orange" alt="Sources">
</p>

<p align="center">
  <a href="#architecture">Architecture</a> ·
  <a href="#coverage">Coverage</a> ·
  <a href="#quick-start">Quick Start</a> ·
  <a href="#repository-layout">Layout</a> ·
  <a href="#development">Validation</a> ·
  <a href="./README.md">中文</a>
</p>

A Python toolkit for **A-share research, quantitative analysis, and market-data engineering**. It provides a consistent interface over multiple public data sources covering quotes, K-lines, financial statements, disclosures, research reports, capital data, historical valuation, macro indicators, and official exchange event datasets.

## Documentation

| Document | Purpose |
|---|---|
| [README.md](./README.md) | Chinese documentation |
| [SKILL.md](./SKILL.md) | Data-routing guide for AI / agent workflows |
| [Data sources](./docs/data-sources_en.md) | Source coverage, stability, and limitations |
| [API reference](./docs/api-reference_en.md) | Python API and usage examples |
| [CHANGELOG.md](./CHANGELOG.md) | Release history |

## Highlights

- **Unified entry point** through `AShareData` for common operations.
- **Multi-source design** using Tencent, Sina, CNINFO, Eastmoney, baostock, NBS, SSE, and HKEX.
- **Traceable output** with fields such as `source`, `source_url`, `fetched_at`, and content hashes where practical.
- **Explicit failures** instead of silently turning upstream errors into empty datasets.
- **Rate-aware access** for Eastmoney endpoints through serialized requests and bounded retries.
- **Provider-oriented architecture** that can be extended with additional exchange and official datasets.

## Architecture

~~~text
stock-data-share
│
├── Unified facade: AShareData
│   ├── Quotes / K-lines ───────── Tencent Finance
│   ├── Financial statements ──── Sina Finance
│   └── Disclosures ───────────── CNINFO
│
├── Specialized providers
│   ├── Company / research / capital data ─ Eastmoney
│   ├── Historical valuation ────────────── baostock
│   ├── PMI ─────────────────────────────── NBS
│   ├── ETF PCF / regulatory events ─────── SSE
│   └── Stock Connect eligibility ───────── HKEX
│
├── Core
│   ├── Symbol normalization
│   └── HTTP sessions / throttling / retries
│
└── Docs / Tests / Examples / Agent Guide
~~~

Common operations use the facade, specialized datasets stay behind provider boundaries, and shared infrastructure lives under `core`.

## Coverage

| Layer | Main capabilities | Primary source |
|---|---|---|
| Quote | Price, change, PE/PB, market cap, turnover, limits | Tencent Finance |
| K-line | Daily; 1/5/15/30/60-minute; qfq/hfq/raw | Tencent Finance |
| Financials | Balance sheet, income statement, cash-flow statement | Sina Finance |
| Disclosures | Shanghai/Shenzhen/Beijing announcements and attachments | CNINFO |
| Company profile | Industry, shares, market cap, listing date | Eastmoney |
| Research | Stock/industry reports, ratings, EPS forecasts, PDFs | Eastmoney |
| Capital data | Margin trading, block trades, holder count, dividends, fund-flow history | Eastmoney |
| Historical valuation | PE/PB/PS/PCF, turnover, trading status, ST flag | baostock |
| Macro | Manufacturing, non-manufacturing, and composite PMI | NBS |
| Official ETF files | PCF basket and cash-substitution parameters | SSE |
| Regulatory events | Listed-company regulatory measures and disciplinary records | SSE |
| Stock Connect | Eligible and sell-only security lists | HKEX |

See [docs/data-sources_en.md](./docs/data-sources_en.md) for source details.

## Installation

~~~bash
git clone https://github.com/quant-stock-data/stock-data-share.git
cd stock-data-share
pip install -e .
~~~

For historical valuation:

~~~bash
pip install -e ".[history]"
~~~

For development:

~~~bash
pip install -e ".[dev,history]"
~~~

## Quick start

~~~python
from ashare_data import AShareData

api = AShareData()

print(api.quote("600519"))
print(api.daily_kline("600519", limit=20, adjust="qfq")[-5:])
print(api.minute_kline("600519", period="m5", limit=20)[-5:])
print(api.financials("600519", statement="income", periods=4))
print(api.announcements("600519", page_size=10))
~~~

### Additional providers

~~~python
api.eastmoney.stock_info("600519")
api.eastmoney.research_reports("600519", pages=1, page_size=20)
api.eastmoney.margin_trading("600519", limit=20)
api.eastmoney.block_trades("600519", limit=20)
api.eastmoney.holder_count("600519", limit=12)
api.eastmoney.dividends("600519", limit=20)

api.baostock.valuation_history("600519", "2025-01-01", "2026-09-30")
api.nbs.pmi()
api.sse.etf_pcf("510180")
api.sse.regulatory_measures("600519", page_size=20)
api.hkex.stock_connect_eligible("sse")
~~~

## CLI

~~~bash
ashare-data quote 600519
ashare-data kline 600519 --period day --limit 20 --adjust qfq
ashare-data kline 600519 --period m5 --limit 20
ashare-data financials 600519 --statement income --periods 4
ashare-data announcements 600519 --limit 10
ashare-data pmi
~~~

## Symbol formats

~~~text
600519
sh600519
600519.SH
bj920982
~~~

A bare `000xxx` symbol is treated as a Shenzhen stock. Use an explicit prefix such as `sh000001` for a Shanghai index.

## Repository layout

~~~text
stock-data-share/
├─ .github/workflows/
├─ docs/
├─ examples/
├─ src/ashare_data/
│  ├─ client.py
│  ├─ cli.py
│  ├─ core/
│  │  ├─ http.py
│  │  └─ symbols.py
│  └─ providers/
│     ├─ tencent.py
│     ├─ sina.py
│     ├─ cninfo.py
│     ├─ eastmoney.py
│     ├─ baostock.py
│     ├─ nbs.py
│     └─ official.py
├─ tests/
├─ CHANGELOG.md
├─ LICENSE
├─ NOTICE
├─ README.md
├─ README_en.md
├─ SKILL.md
└─ pyproject.toml
~~~

## Reliability model

Public web interfaces can change without notice. The project therefore:

1. raises explicit parameter and schema errors;
2. serializes rate-sensitive requests;
3. keeps source metadata where practical;
4. separates live smoke checks from unit tests;
5. reports source failures independently rather than hiding them behind empty results.

Local verification on 2026-09-30: unit tests passed and Ruff checks passed. Most live-source checks returned successfully; some Eastmoney endpoints can occasionally be affected by network-specific connection resets.

## Development

~~~bash
pytest -q
ruff check src tests
python tests/smoke_live.py
~~~

The live smoke suite reaches real external data sources and is intended for manual verification before releases or after upstream changes.

## Roadmap

- SZSE regulatory actions, disciplinary decisions, and inquiries
- SZSE ETF PCF files
- Shanghai/Shenzhen/Beijing IPO, refinancing, and M&A review events
- Historical Stock Connect eligibility changes
- CSI index constituent-change events
- Unified result models, caching, and local persistence

## Contact

<p align="center">
  <img src="./assets/wechat-qrcode.png" width="260" alt="WeChat QR code">
  &nbsp;&nbsp;&nbsp;&nbsp;
  <img src="./assets/qq-qrcode.png" width="260" alt="QQ QR code">
</p>

<p align="center"><b>WeChat · QQ</b></p>

---

## Acknowledgements

Public-interface research was informed in part by Simon Lin's [a-stock-data](https://github.com/simonlin1212/a-stock-data). This repository uses an independent code structure and implementation. See [NOTICE](./NOTICE) for details.

## License

[Apache License 2.0](./LICENSE)

This project provides data-access and research tooling only and does not constitute investment advice.
