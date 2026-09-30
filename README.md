<p align="center"><b>简体中文</b> · <a href="./README_en.md">English</a></p>

<h1 align="center">stock-data-share</h1>

<p align="center"><b>A 股研究与量化数据工具包 · 多源路由 · 官方数据补充 · 来源可追踪</b></p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/version-0.1.0-2ea44f" alt="Version">
  <img src="https://img.shields.io/badge/license-Apache--2.0-blue" alt="License">
  <img src="https://img.shields.io/badge/sources-8-orange" alt="Sources">
</p>

<p align="center">
  <a href="#架构">架构</a> ·
  <a href="#能力地图">能力地图</a> ·
  <a href="#快速开始">快速开始</a> ·
  <a href="#项目结构">项目结构</a> ·
  <a href="#数据源">数据源</a> ·
  <a href="#开发与验证">验证</a>
</p>

一个面向 **A 股研究、量化分析和数据工程** 的 Python 数据工具包。项目将多个公开数据源封装为统一接口，覆盖行情、K 线、财务、公告、研报、资金面、历史估值、宏观指标和交易所官方事件数据，并尽可能保留来源信息，方便核验、归档和二次开发。

---

## 架构

```text
stock-data-share
│
├── 统一入口 AShareData
│   ├── 行情 / K 线 ───────── 腾讯财经
│   ├── 财务报表 ─────────── 新浪财经
│   └── 公告 ─────────────── 巨潮资讯
│
├── 专项数据 Providers
│   ├── 公司资料 / 研报 / 资金面 ─ 东方财富
│   ├── 历史估值 ─────────────── baostock
│   ├── PMI ─────────────────── 国家统计局
│   ├── ETF PCF / 监管事件 ───── 上交所
│   └── 沪深股通资格 ─────────── 港交所
│
├── Core
│   ├── 股票代码标准化
│   └── HTTP 会话 / 限流 / 重试
│
└── Docs / Tests / Examples / Agent Guide
```

常用能力通过 `AShareData` 统一调用；专项数据保留独立 Provider；公共基础逻辑集中在 `core`，让各数据源之间保持低耦合。

---

## 能力地图

| 数据层 | 主要能力 | 主来源 |
|---|---|---|
| 实时行情 | 最新价、涨跌幅、PE/PB、市值、换手率、涨跌停价 | 腾讯财经 |
| K 线 | 日线；1/5/15/30/60 分钟；前复权/后复权/不复权 | 腾讯财经 |
| 财务报表 | 资产负债表、利润表、现金流量表 | 新浪财经 |
| 公告 | 沪深北公告检索、详情页、附件链接 | 巨潮资讯 |
| 公司资料 | 行业、总股本、流通股、市值、上市日期 | 东方财富 |
| 研报 | 个股研报、行业研报、评级、EPS 预测、PDF 链接 | 东方财富 |
| 资金面 | 融资融券、大宗交易、股东户数、分红、资金流历史 | 东方财富 |
| 历史估值 | PE/PB/PS/PCF、换手率、交易状态、ST 标记 | baostock |
| 宏观 | 制造业 PMI、非制造业商务活动、综合 PMI | 国家统计局 |
| ETF 官方文件 | PCF 申购赎回清单、成分篮子、现金替代参数 | 上交所 |
| 监管事件 | 上市公司监管措施、处分记录 | 上交所 |
| 沪深股通资格 | 可买卖名单、sell-only 名单 | 港交所 |

更完整的数据源说明见 [docs/data-sources.md](./docs/data-sources.md)。

---

## 快速开始

### 1. 克隆项目

```bash
git clone https://github.com/quant-stock-data/stock-data-share.git
cd stock-data-share
```

### 2. 安装

```bash
pip install -e .
```

需要历史估值：

```bash
pip install -e ".[history]"
```

开发环境：

```bash
pip install -e ".[dev,history]"
```

### 3. 使用

```python
from ashare_data import AShareData

api = AShareData()

# 实时行情
print(api.quote("600519"))

# 前复权日 K
print(api.daily_kline("600519", limit=20, adjust="qfq")[-5:])

# 5 分钟 K
print(api.minute_kline("600519", period="m5", limit=20)[-5:])

# 利润表
print(api.financials("600519", statement="income", periods=4))

# 公告
print(api.announcements("600519", page_size=10))
```

---

## 专项数据示例

```python
# 公司资料
api.eastmoney.stock_info("600519")

# 个股研报
api.eastmoney.research_reports("600519", pages=1, page_size=20)

# 行业研报
api.eastmoney.industry_reports(pages=1, page_size=20)

# 融资融券
api.eastmoney.margin_trading("600519", limit=20)

# 大宗交易
api.eastmoney.block_trades("600519", limit=20)

# 股东户数
api.eastmoney.holder_count("600519", limit=12)

# 分红
api.eastmoney.dividends("600519", limit=20)

# 历史估值
api.baostock.valuation_history("600519", "2025-01-01", "2026-09-30")

# 最新 PMI
api.nbs.pmi()

# 上交所 ETF PCF
api.sse.etf_pcf("510180")

# 上交所监管事件
api.sse.regulatory_measures("600519", page_size=20)

# 港交所沪股通资格清单
api.hkex.stock_connect_eligible("sse")
```

---

## CLI

```bash
ashare-data quote 600519
ashare-data kline 600519 --period day --limit 20 --adjust qfq
ashare-data kline 600519 --period m5 --limit 20
ashare-data financials 600519 --statement income --periods 4
ashare-data announcements 600519 --limit 10
ashare-data pmi
```

---

## 股票代码格式

支持：

```text
600519
sh600519
600519.SH
bj920982
```

裸 `000xxx` 默认按深市股票处理；如果表示上证指数，请显式写成 `sh000001`。

---

## 项目结构

```text
stock-data-share/
├─ .github/
│  └─ workflows/
│     └─ ci.yml
├─ docs/
│  ├─ api-reference.md
│  ├─ api-reference_en.md
│  ├─ data-sources.md
│  └─ data-sources_en.md
├─ examples/
│  └─ basic_usage.py
├─ src/
│  └─ ashare_data/
│     ├─ client.py
│     ├─ cli.py
│     ├─ core/
│     │  ├─ http.py
│     │  └─ symbols.py
│     └─ providers/
│        ├─ tencent.py
│        ├─ sina.py
│        ├─ cninfo.py
│        ├─ eastmoney.py
│        ├─ baostock.py
│        ├─ nbs.py
│        └─ official.py
├─ tests/
├─ CHANGELOG.md
├─ LICENSE
├─ NOTICE
├─ README.md
├─ README_en.md
├─ SKILL.md
└─ pyproject.toml
```

---

## 数据源

项目采用多来源组合，不把所有能力压在单一网站上。

| 来源 | 主要用途 | 接入方式 |
|---|---|---|
| 腾讯财经 | 实时行情、日 K、分钟 K | HTTP |
| 新浪财经 | 财务三表 | HTTP |
| 巨潮资讯 | 上市公司公告 | HTTP |
| 东方财富 | 公司资料、研报、两融、大宗、股东户数、分红、资金流 | HTTP |
| baostock | 历史估值、上市基础信息 | Python client |
| 国家统计局 | PMI | 官方网页 |
| 上交所 | ETF PCF、监管事件 | 官方接口 / XML |
| 港交所 | Stock Connect 资格清单 | 官方 CSV |

对于容易受访问频率影响的数据源，项目统一使用限流、有限重试和显式错误处理。

---

## 文档

| 文档 | 内容 |
|---|---|
| [README_en.md](./README_en.md) | English documentation |
| [SKILL.md](./SKILL.md) | AI / Agent 数据路由说明 |
| [docs/data-sources.md](./docs/data-sources.md) | 数据源、用途、稳定性与限制 |
| [docs/api-reference.md](./docs/api-reference.md) | Python API 与参数示例 |
| [CHANGELOG.md](./CHANGELOG.md) | 版本更新记录 |

---

## 开发与验证

```bash
pytest -q
ruff check src tests
python tests/smoke_live.py
```

单元测试负责本地逻辑；`smoke_live.py` 会访问真实外部数据源，用于发布前或上游接口变化后的连通性检查。

---

## Roadmap

- 深交所监管措施、纪律处分与问询数据
- 深交所 ETF PCF / 申购赎回清单
- 沪深北 IPO、再融资、并购审核事件
- 港交所 Stock Connect 名单变更历史
- 中证指数样本调整事件
- 统一返回模型、缓存与本地存储层

---

## 联系方式

<p align="center">
  <img src="./assets/wechat-qrcode.png" width="260" alt="微信二维码">
  &nbsp;&nbsp;&nbsp;&nbsp;
  <img src="./assets/qq-qrcode.png" width="260" alt="QQ二维码">
</p>

<p align="center"><b>微信 · QQ</b></p>

---

## 致谢

项目在公开接口调研阶段参考过 Simon Lin 的 [a-stock-data](https://github.com/simonlin1212/a-stock-data) 项目。当前仓库使用独立代码结构与实现，相关说明见 [NOTICE](./NOTICE)。

## License

[Apache License 2.0](./LICENSE)

本项目仅用于数据访问、研究与软件开发，不构成投资建议。
