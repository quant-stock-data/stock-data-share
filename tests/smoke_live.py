"""Live smoke checks. Run manually: python tests/smoke_live.py.

Each upstream is checked independently. One blocked/changed provider should not hide
the status of the remaining providers.
"""

from ashare_data import AShareData


def main():
    api = AShareData(eastmoney_min_interval=2.0)
    checks: dict[str, dict] = {}

    def check(name, fn):
        try:
            ok = bool(fn())
            checks[name] = {"ok": ok, "error": None if ok else "returned empty/false"}
        except Exception as exc:  # noqa: BLE001 - live diagnostics must isolate upstream failures
            checks[name] = {"ok": False, "error": f"{type(exc).__name__}: {exc}"}

    check("tencent_quote", lambda: api.quote("600519").get("name"))
    check("tencent_day", lambda: api.daily_kline("600519", limit=5))
    check("tencent_m5", lambda: api.minute_kline("600519", period="m5", limit=5))
    check("sina_finance", lambda: api.financials("600519", periods=2))
    check("cninfo", lambda: api.announcements("600519", page_size=2))
    check("eastmoney_profile", lambda: api.eastmoney.stock_info("600519").get("name"))
    check("eastmoney_reports", lambda: api.eastmoney.research_reports("600519", pages=1, page_size=3))
    check("eastmoney_industry_reports", lambda: api.eastmoney.industry_reports(pages=1, page_size=3))
    check("eastmoney_margin", lambda: api.eastmoney.margin_trading("600519", limit=2))
    check("eastmoney_block_trade", lambda: api.eastmoney.block_trades("600519", limit=2))
    check("eastmoney_holder_count", lambda: api.eastmoney.holder_count("600519", limit=2))
    check("eastmoney_dividends", lambda: api.eastmoney.dividends("600519", limit=2))
    check("eastmoney_fund_flow", lambda: api.eastmoney.fund_flow_history("600519", limit=5))
    check("baostock_basic", lambda: api.baostock.stock_basic("600519").get("code") == "sh.600519")
    check(
        "baostock_valuation",
        lambda: not api.baostock.valuation_history("600519", "2026-09-01", "2026-09-29").empty,
    )
    check("nbs_pmi", lambda: api.nbs.pmi().get("manufacturing_pmi") is not None)
    def pcf_is_valid():
        pcf = api.sse.etf_pcf("510180")
        return pcf.get("record_number", 0) == len(pcf.get("components") or []) > 0

    check("sse_etf_pcf", pcf_is_valid)
    check("sse_regulatory", lambda: api.sse.regulatory_measures(page_size=3))
    check("hkex_connect", lambda: api.hkex.stock_connect_eligible("sse").get("row_count", 0) > 0)

    for name, result in checks.items():
        suffix = "OK" if result["ok"] else f"FAIL - {result['error']}"
        print(f"{name:28} {suffix}")

    failed = [name for name, result in checks.items() if not result["ok"]]
    if failed:
        print(f"\n{len(failed)} live checks unavailable/failed: {', '.join(failed)}")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
