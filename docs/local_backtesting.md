# Local Python Backtesting

Local backtesting means you provide historical price data, then a Python script simulates what your strategy would have done in the past.

## Basic Flow

1. Get historical daily data as CSV.
2. Load `Date` and `Close` prices.
3. Calculate indicators, like 50-day and 200-day moving averages.
4. Simulate orders.
5. Track portfolio value.
6. Compare against buy and hold.

## CSV Format

The script expects at least these columns:

```csv
Date,Close
2020-01-02,216.16
2020-01-03,214.18
```

Common Yahoo-style CSV files also work if they include `Date` and `Close` or `Adj Close`.

## Run

```bash
python3 src/backtest_sma.py --csv data/QQQ.csv --fast 50 --slow 200 --cash 10000
```

## What It Prints

- Strategy Return
- Buy & Hold Return
- Strategy End Equity
- Buy & Hold End Equity
- Max Drawdown
- Total Orders

## Current Limitation

This first version is intentionally simple. It does not model dividends, slippage, taxes, borrow costs, intraday fills, or realistic order execution.
