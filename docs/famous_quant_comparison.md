# Famous Quant Strategy Comparison vs SPY

Generated with:

```bash
.venv/bin/python -m src.research.run_leaderboard --benchmark SPY --output-name famous_quant_vs_spy
```

Report:

```text
/Users/minhaeng/workspace/trader_agent/reports/famous_quant_vs_spy.html
```

## Test Setup

| Field | Value |
| --- | --- |
| Benchmark | SPY buy and hold |
| Start Cash | $3,000 |
| Date Range | 2016-01-04 to 2026-06-08 |
| Percent Fee | 0.01% |
| Fixed Fee | $0.25 per order |
| Slippage | 0.05% |
| Strategy Count | 602 |

The current Alpaca cache starts at 2016-01-04 for the tested ETFs.

## SPY Benchmark

| Strategy | Return | CAGR | Max DD | Sharpe | Trades | Score |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Buy & Hold SPY | 330.93% | 15.04% | 33.79% | 1.067 | 1 | 99.92 |

## Best By Famous Strategy Family

| Family | Best Candidate | Return | Max DD | Sharpe | Trades | Score | Beats SPY Return | Beats SPY Score |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- | --- |
| Asset buy hold | Buy & Hold GLD | 286.11% | 22.00% | 1.063 | 1 | 117.27 | no | yes |
| Static blend | Permanent Portfolio | 157.26% | 19.43% | 1.290 | 4 | 113.64 | no | yes |
| Risk parity | Quarterly Risk Parity Global Macro | 116.52% | 14.16% | 1.348 | 128 | 110.11 | no | yes |
| Dual momentum | Dual Momentum SPY/EFA 252D | 76.58% | 39.15% | 0.521 | 21 | 46.39 | no | no |
| Cross-sectional momentum | Top-2 ETF Momentum 252D | 152.93% | 18.34% | 0.876 | 135 | 94.05 | no | no |
| Momentum rotation | Momentum Rotation 63/100 | 350.20% | 35.29% | 0.798 | 127 | 72.43 | yes | no |
| Pairs/stat arb | Pairs Mean Reversion QQQ/SPY 60D z2.0 | -6.71% | 12.10% | -0.230 | 86 | 45.43 | no | no |
| Volatility target | Monthly QQQ Vol Target 25% | 636.22% | 32.33% | 1.147 | 90 | 112.56 | yes | yes |

## Most Useful Current Candidates

| Candidate | Why It Matters |
| --- | --- |
| Monthly QQQ Vol Target 25% | Best famous-style candidate that beats SPY by return and score, but trade count is high for a small account. |
| QQQ 95% / QLD 5% | Simple, low-turnover return improvement over SPY, but drawdown is higher than SPY. |
| Permanent Portfolio | Much lower drawdown and higher Sharpe than SPY, but much lower return. Defensive, not growth-oriented. |
| Quarterly Risk Parity Global Macro | Lowest drawdown among useful candidates, but too many trades and much lower return. |
| Buy & Hold QQQ | The brutal baseline: it beats SPY strongly with only one trade. Hard to beat after costs. |

## Current Takeaway

The famous strategy families do not magically beat SPY when reduced to simple ETF versions.

The strongest growth result is still mostly explained by holding more Nasdaq or more leverage. The strongest defensive result comes from gold, bonds, and risk parity. The hard part is combining both without too much turnover or drawdown.

For this project, the next practical research path is:

1. Treat `Buy & Hold QQQ` as the new growth benchmark, not just SPY.
2. Treat `Monthly QQQ Vol Target 25%` as the best famous-style growth/risk candidate.
3. Treat `QQQ 95% / QLD 5%` as the simplest low-turnover aggressive baseline.
4. Reject the current dual momentum and pairs-trading implementations unless they improve in regime tests.
