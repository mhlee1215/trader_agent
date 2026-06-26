# Backtesting Library Shortlist

Goal: avoid building a backtesting engine from scratch. Use an existing Python framework, then connect data from Alpaca or CSV.

## Recommended Path

Use `vectorbt` first.

Why:

- Fast parameter sweeps.
- Good for comparing many SMA/volatility/momentum variants.
- Works naturally with pandas price data.
- Easy to compare strategy portfolios against buy and hold.
- Good fit for local research before paper trading.

Pair it with:

- `alpaca-py` for historical bars and paper trading.
- `pandas` for data handling.
- `plotly` or vectorbt plots for charts.

## Candidates

| Library | Best For | Pros | Cons | Fit |
| --- | --- | --- | --- | --- |
| vectorbt | Fast research and parameter sweeps | Very fast, concise, strong analytics, good charts | Less beginner-friendly for event-driven live trading | Best first choice |
| backtesting.py | Simple one-asset strategies | Small, readable, quick to learn, good visual reports | Not ideal for multi-asset portfolio rotation | Good beginner fallback |
| Backtrader | Event-driven backtests and broker-like flow | Mature, many examples, Alpaca integration exists | Older ecosystem, can feel heavy | Good if we want broker-style simulation |
| PyBroker | ML and walk-forward testing | Supports Alpaca/Yahoo/custom data, ML-oriented | Another framework to learn | Good later |
| Freqtrade | Crypto bot backtesting and live trading | Full bot system, backtesting, reports | Crypto-focused, not ideal for SPY/QQQ/Alpaca stocks | Not for this project now |

## GitHub Repositories Checked

| Repository | Role | Use It? | Notes |
| --- | --- | --- | --- |
| `polakowo/vectorbt` | Research backtester | Yes | Best fit for local strategy sweeps and comparing many parameter combinations. |
| `kernc/backtesting.py` | Simple backtester | Maybe | Good for learning and one-symbol strategies, but weaker for portfolio rotation. |
| `mementum/backtrader` / Backtrader ecosystem | Event-driven backtester | Maybe later | Mature and broker-like, but heavier and older. |
| `alpacahq/alpaca-py` | Alpaca official SDK | Yes | Use for Alpaca market data and paper trading. |
| `alpacahq/alpaca-backtrader-api` | Alpaca + Backtrader bridge | Maybe later | Useful if we choose Backtrader for live/paper flow. |
| `Lumiwealth/lumibot` | Backtest/paper/live framework | Maybe | Interesting because it supports Alpaca and real brokers, but more framework than we need right now. |
| `edtechre/pybroker` | ML-oriented backtester | Later | Good for walk-forward and ML experiments, not needed for the first ETF strategy lab. |
| `freqtrade/freqtrade` | Full crypto bot | No | Strong project, but crypto-focused rather than Alpaca ETF trading. |
| random Alpaca bot repos | Example bots | No | Usually too narrow, old, or risky to adopt as the base. Use them only for reference ideas. |

## Decision

Start with:

```text
Alpaca historical data
→ pandas DataFrame
→ vectorbt backtest
→ compare against buy and hold
→ export results to CSV/Markdown
```

Then later:

```text
Best vectorbt strategy
→ Alpaca Paper Trading bot
```

## First Strategy Set

- QQQ buy and hold baseline.
- QQQ SMA 50/200.
- QQQ partial exposure 100/50.
- QQQ volatility targeting.
- QQQ/SPY/IEF/GLD defensive rotation, only if simpler strategies fail.
