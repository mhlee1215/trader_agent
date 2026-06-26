import argparse
import csv
import math
from collections import deque
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


@dataclass
class Bar:
    date: datetime
    close: float


@dataclass
class BacktestResult:
    strategy_return: float
    buy_hold_return: float
    strategy_end_equity: float
    buy_hold_end_equity: float
    max_drawdown: float
    total_orders: int


def load_bars(path: Path) -> list[Bar]:
    bars: list[Bar] = []

    with path.open(newline="") as file:
        reader = csv.DictReader(file)
        for row in reader:
            date_text = row.get("Date") or row.get("date") or row.get("timestamp")
            close_text = row.get("Close") or row.get("close") or row.get("Adj Close")

            if not date_text or not close_text:
                raise ValueError("CSV must include Date and Close columns")

            bars.append(Bar(date=parse_date(date_text), close=float(close_text)))

    bars.sort(key=lambda bar: bar.date)
    return bars


def parse_date(value: str) -> datetime:
    value = value.strip()
    for date_format in ("%Y-%m-%d", "%Y-%m-%d %H:%M:%S", "%m/%d/%Y"):
        try:
            return datetime.strptime(value[:19], date_format)
        except ValueError:
            pass

    raise ValueError(f"Unsupported date format: {value}")


def simple_moving_average(values: deque[float]) -> float:
    return sum(values) / len(values)


def run_sma_backtest(
    bars: list[Bar],
    fast_period: int,
    slow_period: int,
    initial_cash: float,
) -> BacktestResult:
    if fast_period >= slow_period:
        raise ValueError("fast_period must be less than slow_period")

    if len(bars) <= slow_period:
        raise ValueError("Not enough bars for the requested moving averages")

    cash = initial_cash
    shares = 0.0
    orders = 0
    equity_curve: list[float] = []

    fast_window: deque[float] = deque(maxlen=fast_period)
    slow_window: deque[float] = deque(maxlen=slow_period)

    first_price = bars[0].close
    buy_hold_shares = initial_cash / first_price

    for bar in bars:
        fast_window.append(bar.close)
        slow_window.append(bar.close)

        equity = cash + shares * bar.close
        equity_curve.append(equity)

        if len(slow_window) < slow_period:
            continue

        fast = simple_moving_average(fast_window)
        slow = simple_moving_average(slow_window)
        invested = shares > 0

        if fast > slow and not invested:
            shares = cash / bar.close
            cash = 0.0
            orders += 1
        elif fast < slow and invested:
            cash = shares * bar.close
            shares = 0.0
            orders += 1

    last_price = bars[-1].close
    strategy_end = cash + shares * last_price
    buy_hold_end = buy_hold_shares * last_price

    return BacktestResult(
        strategy_return=percentage_return(initial_cash, strategy_end),
        buy_hold_return=percentage_return(initial_cash, buy_hold_end),
        strategy_end_equity=strategy_end,
        buy_hold_end_equity=buy_hold_end,
        max_drawdown=max_drawdown(equity_curve),
        total_orders=orders,
    )


def percentage_return(start_value: float, end_value: float) -> float:
    return (end_value / start_value - 1.0) * 100.0


def max_drawdown(equity_curve: list[float]) -> float:
    peak = -math.inf
    worst = 0.0

    for equity in equity_curve:
        peak = max(peak, equity)
        drawdown = (equity / peak - 1.0) * 100.0
        worst = min(worst, drawdown)

    return abs(worst)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run a simple SMA crossover backtest from CSV data.")
    parser.add_argument("--csv", required=True, type=Path, help="CSV file with Date and Close columns")
    parser.add_argument("--fast", default=50, type=int, help="Fast SMA period")
    parser.add_argument("--slow", default=200, type=int, help="Slow SMA period")
    parser.add_argument("--cash", default=10000.0, type=float, help="Initial cash")
    args = parser.parse_args()

    bars = load_bars(args.csv)
    result = run_sma_backtest(
        bars=bars,
        fast_period=args.fast,
        slow_period=args.slow,
        initial_cash=args.cash,
    )

    print(f"Strategy Return: {result.strategy_return:.2f}%")
    print(f"Buy & Hold Return: {result.buy_hold_return:.2f}%")
    print(f"Strategy End Equity: ${result.strategy_end_equity:,.2f}")
    print(f"Buy & Hold End Equity: ${result.buy_hold_end_equity:,.2f}")
    print(f"Max Drawdown: {result.max_drawdown:.2f}%")
    print(f"Total Orders: {result.total_orders}")


if __name__ == "__main__":
    main()
