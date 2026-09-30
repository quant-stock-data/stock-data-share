from __future__ import annotations

import argparse
import json

from .client import AShareData


def _dump(value) -> None:
    print(json.dumps(value, ensure_ascii=False, indent=2, default=str))


def main() -> None:
    parser = argparse.ArgumentParser(prog="ashare-data", description="Non-tick A-share public data toolkit")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("quote")
    p.add_argument("symbol")

    p = sub.add_parser("kline")
    p.add_argument("symbol")
    p.add_argument("--period", default="day", help="day or m1/m5/m15/m30/m60")
    p.add_argument("--limit", type=int, default=20)
    p.add_argument("--adjust", choices=["qfq", "hfq", "none"], default="qfq")

    p = sub.add_parser("announcements")
    p.add_argument("symbol")
    p.add_argument("--limit", type=int, default=10)

    p = sub.add_parser("financials")
    p.add_argument("symbol")
    p.add_argument("--statement", choices=["income", "balance", "cashflow"], default="income")
    p.add_argument("--periods", type=int, default=4)

    p = sub.add_parser("pmi")

    args = parser.parse_args()
    api = AShareData()
    if args.command == "quote":
        _dump(api.quote(args.symbol))
    elif args.command == "kline":
        if args.period == "day":
            _dump(api.daily_kline(args.symbol, limit=args.limit, adjust=args.adjust)[-args.limit:])
        else:
            _dump(api.minute_kline(args.symbol, period=args.period, limit=args.limit)[-args.limit:])
    elif args.command == "announcements":
        _dump(api.announcements(args.symbol, page_size=args.limit))
    elif args.command == "financials":
        _dump(api.financials(args.symbol, statement=args.statement, periods=args.periods))
    elif args.command == "pmi":
        _dump(api.nbs.pmi())


if __name__ == "__main__":
    main()

