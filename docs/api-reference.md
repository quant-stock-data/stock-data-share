# API 参考

[中文](./api-reference.md) | [English](./api-reference_en.md)

## 统一入口

~~~python
from ashare_data import AShareData

api = AShareData(eastmoney_min_interval=2.0)
~~~

## 行情

### `quote(symbol)`

~~~python
api.quote("600519")
~~~

常见字段包括价格、昨收、开盘、涨跌、最高/最低、成交额、换手率、PE、PB、市值和涨跌停价。

### `daily_kline(symbol, start=None, end=None, limit=320, adjust="qfq")`

~~~python
api.daily_kline("600519", limit=100, adjust="qfq")
~~~

`adjust` 支持 `qfq`、`hfq`、`none`。

### `minute_kline(symbol, period="m5", limit=320)`

~~~python
api.minute_kline("600519", period="m15", limit=100)
~~~

`period` 支持 `m1`、`m5`、`m15`、`m30`、`m60`。

## 财务与公告

### `financials(symbol, statement="income", periods=8)`

~~~python
api.financials("600519", statement="balance", periods=8)
~~~

`statement` 支持 `balance`、`income`、`cashflow`。

### `announcements(symbol, page_size=30)`

~~~python
api.announcements("600519", page_size=20)
~~~

## 东方财富 Provider

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

## baostock Provider

需要安装：

~~~bash
pip install -e ".[history]"
~~~

~~~python
api.baostock.stock_basic("600519")
api.baostock.valuation_history(
    "600519",
    "2020-01-01",
    "2026-09-30",
)
~~~

## 国家统计局

~~~python
api.nbs.pmi()
~~~

## 上交所

~~~python
api.sse.etf_pcf("510180")
api.sse.regulatory_measures("600519", page_size=20)
~~~

## 港交所

~~~python
api.hkex.stock_connect_eligible("sse")
api.hkex.stock_connect_eligible("szse")
api.hkex.stock_connect_eligible("sse", sell_only=True)
~~~

## 异常语义

- 无效参数：通常为 `ValueError`
- 上游结构变化或关键字段缺失：通常为 `RuntimeError`
- HTTP 失败：由 `requests` 对应异常向上抛出

调用方应区分“请求失败”和“数据确实为空”。