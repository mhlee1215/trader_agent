# Trader Agent Project Checklist

## 0. Safety Rules

- [x] Keep real API keys out of chat and git.
- [x] Default to paper/dry-run mode.
- [x] Add Alpaca paper API keys to local `.env`.
- [x] Keep `TRADING_KILL_SWITCH=true` until paper trading is intentionally enabled.
- [ ] Never use live Alpaca keys during research.

## 1. Local Harness Scaffold

- [x] Add root `AGENTS.md` harness instructions.
- [x] Pick core stack: `vectorbt` for research, `alpaca-py` for data and paper trading.
- [x] Add dependency list.
- [x] Add sample strategy config.
- [x] Add data fetch command skeleton.
- [x] Add vectorbt research sweep command skeleton.
- [x] Add paper signal command skeleton.
- [x] Add paper order command skeleton with dry-run default.
- [x] Install dependencies locally.
- [x] Verify Alpaca paper credentials.

## 2. Data Layer

- [x] Download daily bars for `QQQ`.
- [x] Download daily bars for `SPY`, `IEF`, `GLD`, and `SHY`.
- [x] Cache CSVs under `data/`.
- [x] Confirm columns are clean and sorted.
- [ ] Compare local QQQ price history against QuantConnect sanity checks.

## 3. Research Layer

- [x] Define standard evaluation metrics.
- [x] Add one-number strategy score.
- [x] Reproduce QQQ buy-and-hold in vectorbt.
- [x] Reproduce QQQ SMA 50/200 in vectorbt.
- [x] Run SMA parameter sweep.
- [x] Save sweep results under `reports/`.
- [x] Record best/worst results in `docs/experiment_log.md`.
- [x] Generate HTML strategy leaderboard.
- [x] Add clickable strategy details and source logic to leaderboard.
- [x] Add multi-select comparison chart to leaderboard.
- [x] Add raw-return and risk-adjusted-score benchmark flags.
- [x] Add volatility-target strategy candidates.
- [x] Add subperiod robustness fields to leaderboard.
- [x] Find at least one candidate that beats QQQ buy-and-hold by both raw return and risk-adjusted score.
- [x] Add realistic small-account cost model for `$3,000` starting cash.
- [x] Include fixed fees, percent fees, and slippage in vectorbt evaluations.
- [x] Add low-turnover trend-blend candidates.
- [x] Add simple QQQ/QLD and QQQ/TQQQ small-tilt candidates.
- [x] Add quarterly volatility-target candidates to reduce turnover.
- [ ] Split tests by market regime.
- [ ] Reject cherry-picked strategies.

## 4. Paper Trading Layer

- [ ] Convert best research strategy into a daily target allocation signal.
- [ ] Run signal generator in dry-run mode.
- [ ] Compare target allocation with current Alpaca paper position.
- [ ] Submit no orders unless target differs from current state.
- [ ] Log every decision.
- [ ] Run paper mode manually before scheduling.
- [ ] Run scheduled paper mode for several weeks.

## 5. Deployment Readiness

- [ ] Add market-hours check.
- [ ] Add duplicate-order protection.
- [ ] Add max allocation check.
- [ ] Add max daily loss check.
- [ ] Add account equity sanity check.
- [ ] Add alerting.
- [ ] Add one-command dry-run report.
- [ ] Only consider live mode after paper trading is stable.

## 6. Paper/Live Pipeline Separation

- [x] Add separate paper/live Alpaca account configuration.
- [x] Add paper/live read-only account status command.
- [x] Keep paper and live credentials in separate env names.
- [x] Support separate `.env.paper` and `.env.live` account env files.
- [x] Add live-specific kill switch.
- [x] Add live max single-order notional limit.
- [x] Add live max total planned notional limit.
- [x] Add duplicate open-order protection.
- [x] Require explicit live confirmation string for live order submission.
- [x] Update daily paper automation to execute paper rebalance.
- [x] Update weekly live automation to execute Monday after market open when `LIVE_AUTO_REBALANCE=true`.
- [x] Add live initial seed setting for `$100` experiment.
- [x] Add explicit `LIVE_CAPITAL_CAP` for live auto-trading budget.
- [ ] Add persistent order/decision logs.
- [ ] Add live order result verification report after first live test.

## Current Next Step

Run regime-split tests for the two tiny TQQQ/QQQ trend-blend candidates before considering paper trading.

```bash
.venv/bin/python -m src.research.run_leaderboard --benchmark QQQ --output-name strategy_leaderboard_3000
```
