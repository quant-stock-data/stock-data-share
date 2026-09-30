from __future__ import annotations

import re
from dataclasses import dataclass

_SYMBOL_RE = re.compile(
    r"^(?:(sh|sz|bj)[.\-]?)?(\d{6})(?:[.\-]?(sh|sz|bj))?$",
    re.IGNORECASE,
)


def _natural_market(code: str) -> str:
    if code.startswith(("92", "4", "8")):
        return "bj"
    if code.startswith(("5", "6", "9")):
        return "sh"
    return "sz"


@dataclass(frozen=True, slots=True)
class Symbol:
    code: str
    market: str

    @property
    def tencent(self) -> str:
        return f"{self.market}{self.code}"

    @property
    def eastmoney_secid(self) -> str:
        # Eastmoney uses 1=SH, 0=SZ/BJ.
        return f"{1 if self.market == 'sh' else 0}.{self.code}"

    @property
    def baostock(self) -> str:
        if self.market not in {"sh", "sz"}:
            raise ValueError("baostock does not support Beijing Stock Exchange symbols")
        return f"{self.market}.{self.code}"


def parse_symbol(raw: str) -> Symbol:
    """Parse 600519 / sh600519 / 600519.SH / bj920982.

    Bare 000xxx is treated as a Shenzhen stock. Use an explicit prefix/suffix
    for Shanghai indexes such as sh000001.
    """
    text = str(raw).strip().lower()
    m = _SYMBOL_RE.fullmatch(text)
    if not m:
        raise ValueError(f"unsupported symbol format: {raw!r}")
    prefix, code, suffix = m.groups()
    if prefix and suffix and prefix != suffix:
        raise ValueError(f"conflicting market prefix/suffix: {raw!r}")
    market = prefix or suffix or _natural_market(code)
    natural = _natural_market(code)
    # 000xxx is intentionally ambiguous (SZ stock vs SH index); explicit SH is allowed.
    if not code.startswith("000") and market != natural:
        raise ValueError(f"market {market} conflicts with symbol {code} (expected {natural})")
    if market == "bj" and code.startswith("000"):
        raise ValueError(f"000xxx cannot be a Beijing Stock Exchange symbol: {raw!r}")
    return Symbol(code=code, market=market)

