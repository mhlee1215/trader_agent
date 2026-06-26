# Strategy Leaderboard

Generate the leaderboard with:

```bash
.venv/bin/python -m src.research.run_leaderboard --benchmark QQQ --output-name strategy_leaderboard_3000
```

Outputs:

- `reports/strategy_leaderboard_3000.csv`
- `reports/strategy_leaderboard_3000.json`
- `reports/strategy_leaderboard_3000.html`

Open the HTML file in a browser:

```text
/Users/minhaeng/workspace/trader_agent/reports/strategy_leaderboard_3000.html
```

## What It Does

- Registers every strategy implemented in `src/research/run_leaderboard.py`.
- Evaluates each strategy with the standard metrics from `docs/evaluation_metrics.md`.
- Computes a one-number score.
- Marks whether each strategy beats QQQ buy-and-hold by raw return.
- Marks whether each strategy beats QQQ buy-and-hold by risk-adjusted score.
- Embeds each strategy's source logic in the detail panel.
- Embeds normalized equity curves for comparison.
- Applies the default small-account cost model: `$3,000` starting cash, `0.01%` fee, `$0.25` fixed order fee, and `0.05%` slippage.

## Current Findings

As of the current run:

- 561 strategies are registered.
- 58 strategies beat QQQ buy-and-hold by raw total return.
- 74 strategies beat QQQ buy-and-hold by the risk-adjusted score.
- 2 strategies beat QQQ buy-and-hold by both raw return and risk-adjusted score.
- The top score candidate is `TQQQ/GLD Trend Blend 20/100 25%`.

Current top candidate:

| Strategy | Return | CAGR | Max DD | Sharpe | Trades | Fees | Score |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| TQQQ/GLD Trend Blend 20/100 25% | 309.46% | 14.48% | 20.04% | 1.183 | 11 | $8.75 | 108.84 |
| QQQ Buy & Hold | 606.25% | 20.63% | 35.00% | 1.152 | 1 | $0.55 | 99.92 |

This candidate improves risk-adjusted score by cutting drawdown, but it does not beat QQQ buy-and-hold by raw return.

Best current candidates that beat QQQ buy-and-hold by both raw return and score:

| Strategy | Return | CAGR | Max DD | Sharpe | Trades | Fees | Score |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| TQQQ/QQQ Trend Blend 20/100 10% | 606.62% | 20.63% | 33.43% | 1.181 | 11 | $7.31 | 102.61 |
| TQQQ/QQQ Trend Blend 20/100 5% | 606.66% | 20.64% | 34.23% | 1.174 | 11 | $6.41 | 101.08 |

These are very small leveraged tilts, not high-conviction live-trading systems yet.

Best simple return-improvement candidate if accepting slightly worse drawdown:

| Strategy | Return | CAGR | Max DD | Sharpe | Trades | Fees | Score |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| QQQ 95% / QLD 5% | 669.67% | 21.63% | 38.31% | 1.128 | 2 | $0.80 | 95.62 |
| QQQ Buy & Hold | 606.25% | 20.63% | 35.00% | 1.152 | 1 | $0.55 | 99.92 |

This is a more meaningful raw-return improvement than the tiny TQQQ trend tilt, but it is not a better risk-adjusted strategy.

## How To Add A New Algorithm

1. Add the strategy logic to `src/research/run_leaderboard.py` or a reusable module under `src/strategies/`.
2. Return a `StrategyResult` with:
   - unique `id`
   - human-readable `name`
   - `family`
   - description
   - source-code snippet
   - vectorbt portfolio result
3. Run the leaderboard command again.
4. Check the new row in the HTML leaderboard.

## Current Caveat

Alpaca data starts at 2016-01-04 for the cached symbols, even when requesting 2010-01-01. Treat current results as 2016-2026 tests unless older adjusted data is added from another source.

Volatility-target strategies can trade often. Under the `$3,000` cost model, many high-return volatility-target candidates lose score because fees, slippage, and turnover are too large.
