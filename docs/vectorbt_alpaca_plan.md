# VectorBT + Alpaca Trading Bot Plan

## Goal

Build a beginner-safe local research system:

```text
Alpaca market data
→ vectorbt backtests
→ strategy comparison reports
→ Alpaca Paper Trading
→ optional live deployment much later
```

This project is for education and paper trading first. Do not connect real-money trading until paper trading has been stable for weeks.

## Phase 1: Local Research Setup

- [ ] Create a Python virtual environment.
- [ ] Install research dependencies:
  - `pandas`
  - `numpy`
  - `vectorbt`
  - `alpaca-py`
  - `python-dotenv`
  - `matplotlib` or `plotly`
- [ ] Keep secrets in local `.env`, never in git.
- [ ] Add Alpaca paper API keys to `.env`.
- [ ] Create a script that verifies Alpaca authentication.
- [ ] Create a script that downloads daily bars for `QQQ`, `SPY`, `IEF`, `GLD`, and `SHY`.
- [ ] Cache downloaded data under `data/` so repeated tests do not call the API every time.

## Phase 2: Reproduce QuantConnect Experiments

- [ ] Rebuild QQQ buy-and-hold baseline in vectorbt.
- [ ] Rebuild QQQ SMA 50/200 strategy.
- [ ] Rebuild QQQ partial exposure strategy.
- [ ] Compare local results against QuantConnect screenshots.
- [ ] Record differences in `docs/experiment_log.md`.
- [ ] Add transaction cost assumptions.
- [ ] Add drawdown, Sharpe, total return, annualized return, and trade count outputs.

## Phase 3: Strategy Search

- [ ] Parameter sweep SMA pairs, such as 20/100, 50/150, 50/200, 100/200.
- [ ] Test volatility targeting.
- [ ] Test monthly rebalancing instead of daily trading.
- [ ] Test simple defensive allocation, but reject strategies that add complexity without improving drawdown or Sharpe.
- [ ] Split tests into periods:
  - 2010-2015
  - 2016-2020
  - 2021-2024
  - full period
- [ ] Reject strategies that only work in one cherry-picked period.

## Phase 4: Paper Trading Bot

- [ ] Convert the best strategy into a daily signal generator.
- [ ] Add a dry-run mode that prints intended orders without submitting them.
- [ ] Add Alpaca Paper Trading order submission.
- [ ] Add current-position checks before submitting new orders.
- [ ] Add max allocation limits.
- [ ] Add a kill switch environment variable.
- [ ] Add logs for every decision and order.
- [ ] Run in paper mode for at least several weeks.

## Phase 5: Deployment

Simple deployment is possible because Alpaca exposes the same API style for paper and live trading. The hard part is operating safely.

- [ ] Run the bot on a scheduled job once per trading day.
- [ ] Use a small VPS, home Mac launchd job, GitHub Actions schedule, or another scheduler.
- [ ] Add process logs and alerting.
- [ ] Add account equity checks.
- [ ] Add maximum daily loss checks.
- [ ] Add duplicate-order protection.
- [ ] Add market-hours checks.
- [ ] Add fail-closed behavior when data or account calls fail.

## Live Trading Readiness Checklist

Do not go live unless all are true:

- [ ] The bot has run successfully in Alpaca Paper Trading for weeks.
- [ ] Backtest and paper behavior are reasonably consistent.
- [ ] The strategy has been tested across multiple market regimes.
- [ ] The strategy does not depend on one lucky period.
- [ ] The bot never submits orders without logging why.
- [ ] The bot has a kill switch.
- [ ] Position size is intentionally small.
- [ ] Real API keys are stored separately from paper API keys.
- [ ] The first live test uses tiny size.

## Recommendation

Start with local vectorbt research and Alpaca historical data. Treat Alpaca Paper Trading as the first deployment target. Treat live trading as an operational safety project, not just a code switch.
