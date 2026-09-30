1	# stock-data-share
2	
3	一个面向 **A 股研究 / 量化取数** 的轻量数据工具包。项目只做 **非 tick 数据**：实时快照、日/分钟 K 线、财务三表、公告、两融/大宗/股东户数/分红、历史估值、宏观 PMI 等。
4	
5	本项目不是把别人的 Skill 原样换皮，而是重新按「provider + 统一代码路由 + 明确错误 + 来源追踪」组织代码；每条输出尽量保留 `source` / `source_url`，方便核对原始来源。
6	
7	## 为什么另做一个
8	
9	- **不提供 tick / 逐笔成交**，也不把逐笔能力藏在别的接口里。
10	- **腾讯作为行情主源**：2026-09 起通达信公开服务器的 K 线/盘口命令已出现返回空数据的问题，因此本项目首版不把 mootdx 行情作为依赖。
11	- **东财统一串行限流**：通过线程锁真正保证同一实例串行请求，默认请求间隔 2 秒；连接错误/429/5xx 做有限退避重试，403 不连续重试。
12	- **数据中心支持分页和显式报错**：不把“来源异常”静默伪装成空数据。
13	- **公告直接走巨潮**，财报三表走新浪，历史估值用 baostock（可选依赖），尽量减少单一来源依赖。
14	
15	## 首版能力
16	
17	| 类别 | 能力 | 主源 |
18	|---|---|---|
19	| 行情 | 实时价、PE/PB、市值、换手率、涨跌停价 | 腾讯财经 |
20	| K 线 | 日线前/后/不复权；1/5/15/30/60 分钟 | 腾讯财经 |
21	| 财务 | 资产负债表、利润表、现金流量表 | 新浪财经 |
22	| 公告 | 沪深北公告检索 + 附件链接 | 巨潮资讯 |
23	| 基本面 | 行业、股本、市值、上市日 | 东财（限流） |
24	| 研报 | 个股/行业研报、评级、EPS 预测、PDF 直链 | 东财 reportapi（限流） |
25	| 资金面 | 融资融券、大宗交易、股东户数、分红；120 日资金流为易风控项 | 东财（限流） |
26	| 历史估值 | PE/PB/PS/PCF、换手、停牌、ST | baostock（可选） |
27	| 宏观 | 最新制造业/非制造业/综合 PMI | 国家统计局 |
28	| 官方 ETF 文件 | PCF 申购赎回清单、篮子、现金替代参数 | 上交所官方 XML |
29	| 官方监管事件 | 上市公司监管措施/处分记录 | 上交所官方查询 |
30	| 沪深股通资格 | 可买卖 / sell-only 官方资格清单 | 港交所官方 CSV |
31	
32	> 说明：2026-09-30 当前环境的完整 live smoke 共 19 项，18 项真实返回成功；
33	> 腾讯实时行情/日线/5 分钟 K、新浪财报、巨潮公告、东财多数数据中心、baostock、
34	> 国家统计局、上交所官方、港交所官方均通过。东财 120 日资金流当次出现连接被上游重置，
35	> 因此明确标成易风控项，不把“偶尔能通”包装成稳定能力。百度股市通同环境返回 HTTP 403，
36	> 首版不列为主能力。
37	
38	## 安装
39	
40	```bash
41	pip install -e .
42	```
43	
44	需要历史估值时：
45	
46	```bash
47	pip install -e ".[history]"
48	```
49	
50	开发/测试：
51	
52	```bash
53	pip install -e ".[dev,history]"
54	pytest -q
55	python tests/smoke_live.py
56	```
57	
58	## 快速使用
59	
60	```python
61	from ashare_data import AShareData
62	
63	api = AShareData()
64	
65	# 实时行情
66	print(api.quote("600519"))
67	
68	# 前复权日 K
69	print(api.daily_kline("600519", limit=20, adjust="qfq")[-5:])
70	
71	# 5 分钟 K（不是逐笔）
72	print(api.minute_kline("600519", period="m5", limit=20)[-5:])
73	
74	# 利润表
75	print(api.financials("600519", statement="income", periods=4))
76	
77	# 公告
78	print(api.announcements("600519", page_size=10))
79	
80	# 上交所 ETF PCF：官方 XML，带内容哈希和成分数量校验
81	pcf = api.sse.etf_pcf("510180")
82	print(pcf["trading_day"], pcf["record_number"])
83	
84	# 上交所监管事件
85	print(api.sse.regulatory_measures("600519", page_size=10))
86	
87	# 港交所发布的沪股通资格清单
88	eligible = api.hkex.stock_connect_eligible("sse")
89	print(eligible["updated"], eligible["row_count"])
90	
91	# 两融
92	print(api.eastmoney.margin_trading("600519", limit=10))
93	
94	# 历史估值（需 baostock 可选依赖）
95	df = api.baostock.valuation_history("600519", "2025-01-01", "2026-09-30")
96	print(df.tail())
97	```
98	
99	CLI：
100	
101	```bash
102	ashare-data quote 600519
103	ashare-data kline 600519 --period m5 --limit 20
104	ashare-data announcements 600519 --limit 5
105	ashare-data financials 600519 --statement income --periods 4
106	ashare-data pmi
107	```
108	
109	## 代码格式
110	
111	支持：
112	
113	- `600519`
114	- `sh600519`
115	- `600519.SH`
116	- `bj920982`
117	
118	裸 `000xxx` 默认按深市股票处理；如果你指的是上证指数，请显式写 `sh000001`。
119	
120	## 数据源与稳定性
121	
122	公共网页/API 不是官方承诺的 SDK，任何来源都可能调整。项目的原则是：
123	
124	1. 参数错误直接 `ValueError`；
125	2. 上游结构异常直接 `RuntimeError`；
126	3. 不把“抓取失败”伪装成“确实没有数据”；
127	4. 东财请求默认串行且留间隔；
128	5. README 只写实际验证过的能力，不用端点数量包装成熟度。
129	
130	## 路线图：增加官方事件型数据
131	
132	已经在首版加入：**SSE ETF PCF、SSE 监管措施、HKEX Stock Connect 资格清单**。
133	
134	下一阶段继续加入与普通行情不同、适合事件研究的官方源：
135	
136	- 深交所监管措施、纪律处分、监管问询；
137	- 沪深北 IPO / 再融资 / 并购审核项目动态；
138	- 深交所 ETF PCF / 申购赎回清单；
139	- 港交所 Stock Connect 名单变更历史；
140	- 中证指数历史调样事件。
141	
142	这些能力会按 `source_url + fetched_at + source_date + content_hash` 保存来源证明，重点解决“历史状态能不能重建”，而不是单纯继续堆接口数量。
143	
144	## License / Attribution
145	
146	Apache-2.0。项目为独立实现，但接口调研思路参考过 Simon Lin 的
147	[`a-stock-data`](https://github.com/simonlin1212/a-stock-data)（Apache-2.0），具体说明见 `NOTICE`。
148	
149	仅提供数据访问与研究工具，不构成投资建议。