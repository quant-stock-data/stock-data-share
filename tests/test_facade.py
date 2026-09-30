from ashare_data import AShareData


def test_facade_exposes_core_providers_and_methods():
    api = AShareData(eastmoney_min_interval=0)

    assert callable(api.quote)
    assert callable(api.daily_kline)
    assert callable(api.minute_kline)
    assert callable(api.financials)
    assert callable(api.announcements)

    assert api.tencent is not None
    assert api.sina is not None
    assert api.cninfo is not None
    assert api.eastmoney is not None
    assert api.baostock is not None
    assert api.nbs is not None
    assert api.sse is not None
    assert api.hkex is not None
