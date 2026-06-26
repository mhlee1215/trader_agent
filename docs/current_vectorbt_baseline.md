# Current VectorBT Baseline

Generated with:

```bash
.venv/bin/python -m src.research.run_leaderboard --benchmark QQQ --output-name strategy_leaderboard_3000
```

## Data

| Field | Value |
| --- | --- |
| Source | Alpaca market data |
| Symbol | QQQ |
| Requested Start | 2010-01-01 |
| Actual Cached Start | 2016-01-04 |
| Cached End | 2026-06-08 |
| Rows | 2622 |

Alpaca returned QQQ daily bars from 2016-01-04 even though the request started at 2010-01-01. Treat this baseline as a 2016-2026 test unless older data is added from another source.

## Evaluation Metrics

The standard metrics are defined in `docs/evaluation_metrics.md`.

Current small-account assumptions:

| Field | Value |
| --- | --- |
| Starting Cash | $3,000 |
| Percent Fee | 0.01% per order |
| Fixed Fee | $0.25 per order |
| Slippage | 0.05% |

Primary comparison fields:

- Total Return [%]
- CAGR [%]
- Max Drawdown [%]
- Sharpe Ratio
- Sortino Ratio
- Calmar Ratio
- Total Trades
- Total Fees Paid
- Fee Drag [%]
- Exposure Time [%]
- Excess Return vs Buy Hold [%]
- Drawdown Improvement vs Buy Hold [%]
- Sharpe Improvement vs Buy Hold

## Baseline Result

| Strategy | Return | CAGR | Max DD | Sharpe | Sortino | Calmar | Trades | Exposure | End Value |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| QQQ Buy & Hold | 606.25% | 20.63% | 35.00% | 1.152 | 1.632 | 0.589 | 1 | 100.00% | $21,187.59 |

## Current Best Score Candidate

| Strategy | Return | CAGR | Max DD | Sharpe | Sortino | Calmar | Trades | Fees | End Value |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| TQQQ/GLD Trend Blend 20/100 25% | 309.46% | 14.48% | 20.04% | 1.183 | 1.677 | 0.722 | 11 | $8.75 | $12,283.94 |

## Interpretation

QQQ Buy & Hold still wins on raw total return and final value versus the top score candidate.

The best current score candidate gives up a lot of raw return, but cuts max drawdown from `35.00%` to `20.04%` and slightly improves Sharpe. This is a defensive/risk-adjusted candidate, not a return-maximizing candidate.

The only current candidates that beat QQQ buy-and-hold by both raw return and score are tiny TQQQ tilts:

| Strategy | Return | CAGR | Max DD | Sharpe | Trades | Fees | Score |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| TQQQ/QQQ Trend Blend 20/100 10% | 606.62% | 20.63% | 33.43% | 1.181 | 11 | $7.31 | 102.61 |
| TQQQ/QQQ Trend Blend 20/100 5% | 606.66% | 20.64% | 34.23% | 1.174 | 11 | $6.41 | 101.08 |

This edge is tiny. Treat it as a research lead, not a paper-trading-ready strategy.

If the objective is higher raw return and slightly worse drawdown is acceptable, the simplest current candidate is:

| Strategy | Return | CAGR | Max DD | Sharpe | Trades | Fees | Score |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| QQQ 95% / QLD 5% | 669.67% | 21.63% | 38.31% | 1.128 | 2 | $0.80 | 95.62 |

This gives a more visible return improvement, but the score rejects it because drawdown and Sharpe are worse than QQQ buy-and-hold.

## Next Research Steps

- Test the same strategy across sub-periods.
- Add older QQQ data from another source if we want true 2010-2026 coverage.
- Add out-of-sample and regime-split tests for the TQQQ/QQQ trend blend.
- Test whether the tiny TQQQ edge survives different date ranges and data providers.
- Prefer low-turnover candidates while account size is around `$3,000`.
- Do not move to paper trading until a strategy survives multi-period testing.

## Leaderboard

The active leaderboard is:

```text
reports/strategy_leaderboard.html
reports/strategy_leaderboard_3000.html
```

It currently tracks both:

- `beats_bh_return`: raw total return above QQQ buy-and-hold.
- `beats_bh_score`: risk-adjusted score above QQQ buy-and-hold.

Current top score candidate:

| Strategy | Return | CAGR | Max DD | Sharpe | Score |
| --- | ---: | ---: | ---: | ---: | ---: |
| TQQQ/GLD Trend Blend 20/100 25% | 309.46% | 14.48% | 20.04% | 1.183 | 108.84 |
| QQQ Buy & Hold | 606.25% | 20.63% | 35.00% | 1.152 | 99.92 |
