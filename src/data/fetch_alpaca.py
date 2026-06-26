import argparse
from datetime import datetime

from src.common.env import load_env, require_env
from src.common.paths import DATA_DIR, ensure_runtime_dirs


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Fetch historical daily bars from Alpaca.")
    parser.add_argument("--symbols", nargs="+", required=True, help="Symbols to fetch, such as QQQ SPY")
    parser.add_argument("--start", default="2010-01-01", help="Start date in YYYY-MM-DD")
    parser.add_argument("--end", default=None, help="End date in YYYY-MM-DD")
    parser.add_argument(
        "--adjustment",
        choices=["raw", "split", "dividend", "all"],
        default="all",
        help="Price adjustment mode. Use 'all' for backtesting.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    ensure_runtime_dirs()

    try:
        import pandas as pd
        from alpaca.data.enums import Adjustment
        from alpaca.data.historical import StockHistoricalDataClient
        from alpaca.data.requests import StockBarsRequest
        from alpaca.data.timeframe import TimeFrame
    except ImportError as exc:
        raise SystemExit("Install dependencies first: python3 -m pip install -r requirements.txt") from exc

    env = load_env()
    client = StockHistoricalDataClient(
        require_env(env, "ALPACA_API_KEY"),
        require_env(env, "ALPACA_SECRET_KEY"),
    )

    request = StockBarsRequest(
        symbol_or_symbols=args.symbols,
        timeframe=TimeFrame.Day,
        start=datetime.fromisoformat(args.start),
        end=datetime.fromisoformat(args.end) if args.end else None,
        adjustment=Adjustment(args.adjustment),
    )

    bars = client.get_stock_bars(request).df
    if bars.empty:
        raise SystemExit("Alpaca returned no bars.")

    for symbol in args.symbols:
        symbol_bars = bars.loc[symbol].reset_index()
        output = DATA_DIR / f"{symbol}_daily.csv"
        symbol_bars.to_csv(output, index=False)
        print(f"Wrote {len(symbol_bars)} rows to {output} adjustment={args.adjustment}")


if __name__ == "__main__":
    main()
