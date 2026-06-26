import argparse
from pathlib import Path

import pandas as pd

from src.strategies.sma import latest_sma_target


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate a simple SMA target allocation signal.")
    parser.add_argument("--csv", default="data/QQQ_daily.csv", type=Path)
    parser.add_argument("--fast", default=50, type=int)
    parser.add_argument("--slow", default=200, type=int)
    parser.add_argument("--uptrend-weight", default=1.0, type=float)
    parser.add_argument("--downtrend-weight", default=0.5, type=float)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    closes = load_closes(args.csv)

    signal = latest_sma_target(
        closes,
        fast=args.fast,
        slow=args.slow,
        uptrend_weight=args.uptrend_weight,
        downtrend_weight=args.downtrend_weight,
    )

    print(f"regime={signal['regime']}")
    print(f"fast_sma={signal['fast_sma']:.2f}")
    print(f"slow_sma={signal['slow_sma']:.2f}")
    print(f"target_weight={signal['target_weight']:.2f}")


def load_closes(path: Path) -> pd.Series:
    prices = pd.read_csv(path)
    close_column = "close" if "close" in prices.columns else "Close"
    return prices[close_column].astype(float)


if __name__ == "__main__":
    main()
