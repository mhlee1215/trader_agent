# Broad Universe Research

Generated reports:

```text
/Users/minhaeng/workspace/trader_agent/reports/broad_universe_vs_spy.html
/Users/minhaeng/workspace/trader_agent/reports/broad_universe_vs_qqq.html
```

Commands:

```bash
.venv/bin/python -m src.research.run_leaderboard --benchmark SPY --output-name broad_universe_vs_spy
.venv/bin/python -m src.research.run_leaderboard --benchmark QQQ --output-name broad_universe_vs_qqq
```

## Data Universe

The broad universe adds:

- Sector ETFs: `XLK`, `XLY`, `XLC`, `XLF`, `XLV`, `XLI`, `XLP`, `XLE`, `XLU`, `XLB`, `XLRE`
- Large-cap stocks: `AAPL`, `MSFT`, `NVDA`, `AMZN`, `META`, `GOOGL`, `GOOG`, `AVGO`, `TSLA`, `COST`, `NFLX`, `AMD`, `ADBE`, `CRM`, `ORCL`, `CSCO`, `INTC`, `IBM`, `QCOM`, `TXN`, `AMAT`, `MU`, `LRCX`, `JPM`, `BAC`, `GS`, `MS`, `V`, `MA`, `UNH`, `LLY`, `JNJ`, `MRK`, `ABBV`, `PFE`, `HD`, `MCD`, `NKE`, `WMT`, `TGT`, `PG`, `KO`, `PEP`, `XOM`, `CVX`, `CAT`, `GE`, `BA`

## Critical Caveat

The large-cap stock universe is a current hand-picked liquid universe. It has survivorship bias because it includes companies known today to be major winners. Treat the results as a research lead, not a tradable conclusion.

Before paper trading, replace this with a point-in-time universe such as historical S&P 500 constituents, Nasdaq 100 constituents, or another survivorship-bias-free dataset.

## SPY Benchmark Result

| Strategy | Return | CAGR | Max DD | Sharpe | Trades | Score |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Buy & Hold SPY | 330.93% | 15.04% | 33.79% | 1.067 | 1 | 99.92 |

Best broad-universe result vs SPY:

| Strategy | Return | CAGR | Max DD | Sharpe | Trades | Fees | Score |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Large-Cap Top-3 Momentum 126D | 6449.17% | 49.36% | 40.65% | 1.718 | 207 | $453.55 | 163.10 |
| Quarterly Large-Cap Top-5 Momentum 63D | 2005.47% | 33.96% | 30.88% | 1.590 | 167 | $169.54 | 156.56 |
| Quarterly Large-Cap Top-5 Momentum 126D | 1959.60% | 33.67% | 34.37% | 1.489 | 146 | $126.89 | 149.82 |

## QQQ Benchmark Result

| Strategy | Return | CAGR | Max DD | Sharpe | Trades | Score |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Buy & Hold QQQ | 606.25% | 20.63% | 35.00% | 1.152 | 1 | 99.92 |

Best broad-universe result vs QQQ:

| Strategy | Return | CAGR | Max DD | Sharpe | Trades | Fees | Score |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Large-Cap Top-3 Momentum 126D | 6449.17% | 49.36% | 40.65% | 1.718 | 207 | $453.55 | 146.97 |
| Quarterly Large-Cap Top-5 Momentum 63D | 2005.47% | 33.96% | 30.88% | 1.590 | 167 | $169.54 | 140.12 |
| Quarterly Large-Cap Top-5 Momentum 126D | 1959.60% | 33.67% | 34.37% | 1.489 | 146 | $126.89 | 133.54 |

## Interpretation

The broader universe finally produces strategies that beat both SPY and QQQ by a wide margin.

However, this is exactly where backtests become dangerous:

- Current-list survivorship bias is probably large.
- Mega-cap tech winners dominate the result.
- The best strategy trades 207 times, which is high for a small account.
- The result may collapse if we use a proper point-in-time universe.

## Next Required Step

Do not move this to paper trading yet.

The next required research step is a survivorship-bias check:

1. Build or import historical index constituent lists.
2. Re-run large-cap momentum using only stocks available at each historical date.
3. Add regime splits and rolling walk-forward validation.
4. Only keep strategies that still beat QQQ after those tests.
