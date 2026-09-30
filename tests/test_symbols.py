import pytest

from ashare_data.core.symbols import parse_symbol


def test_symbol_routes():
    assert parse_symbol("600519").tencent == "sh600519"
    assert parse_symbol("000001").tencent == "sz000001"
    assert parse_symbol("sh000001").tencent == "sh000001"
    assert parse_symbol("600519.SH").tencent == "sh600519"
    assert parse_symbol("920982").tencent == "bj920982"
    assert parse_symbol("510300").tencent == "sh510300"


def test_conflicting_market_rejected():
    with pytest.raises(ValueError):
        parse_symbol("sz600519")
