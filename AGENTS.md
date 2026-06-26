# Trader Agent Instructions

This repository is a beginner-safe trading research harness. The primary stack is:

```text
vectorbt = local strategy research and backtesting
alpaca-py = Alpaca market data and paper trading
QuantConnect = optional UI-only strategy prototyping
```

Do not treat this repository as financial advice or as a ready live-trading system.

## Operating Principles

- Prefer paper trading and dry runs.
- Keep the harness small, explicit, and auditable.
- Use existing libraries for backtesting and broker APIs; do not build a full trading engine from scratch.
- Compare every strategy against a simple buy-and-hold benchmark.
- Optimize for repeatable experiments, logs, and safety gates before performance.
- Reject strategies that add complexity without improving drawdown, Sharpe ratio, or robustness.

## Safety Rules

- Never commit real API keys, tokens, account IDs, or secrets.
- Never ask the user to paste secrets into chat.
- Read secrets from local `.env` only.
- Default trading mode is paper/dry-run.
- Live trading support must not be added casually.
- Any command that can place an order must default to no real order.
- `TRADING_KILL_SWITCH=true` must block order submission.
- Alpaca live keys must not be used in this project until the user explicitly asks for live-mode work.
- Do not submit orders unless current positions have been checked.
- Do not submit orders on failed, missing, or stale data.

## Current Repository Layout

```text
configs/
  qqq_sma.json

docs/
  project_checklist.md
  vectorbt_alpaca_plan.md
  harness_shortlist.md
  experiment_log.md

src/
  common/
  data/
  research/
  paper/
  safety/

strategies/
  QuantConnect-only prototypes
```

## Standard Workflow

1. Update `docs/project_checklist.md` when starting or finishing meaningful harness work.
2. Put strategy assumptions in config files under `configs/`.
3. Fetch or cache market data under `data/`.
4. Run local research through `src/research/`.
5. Save generated reports under `reports/`.
6. Record notable strategy results in `docs/experiment_log.md`.
7. Only convert a strategy to paper trading after it has a saved backtest result.
8. Keep paper order commands dry-run by default.

## Setup

Use the local virtual environment:

```bash
.venv/bin/python -m pip install -r requirements.txt
```

The `.venv` may already exist. Use it for project commands.

## Common Commands

Fetch daily Alpaca bars:

```bash
.venv/bin/python -m src.data.fetch_alpaca --symbols QQQ SPY IEF GLD SHY --start 2010-01-01
```

Run the vectorbt SMA sweep:

```bash
.venv/bin/python -m src.research.run_vectorbt_sweep --config configs/qqq_sma.json
```

Generate a paper-trading signal from cached data:

```bash
.venv/bin/python -m src.paper.generate_signal --csv data/QQQ_daily.csv
```

Preview an Alpaca paper order without submitting it:

```bash
.venv/bin/python -m src.paper.place_order_alpaca --symbol QQQ --notional 100 --side buy
```

## Verification

Run syntax checks after edits:

```bash
.venv/bin/python -m compileall src strategies
```

Run dry-run order preview after paper command changes:

```bash
.venv/bin/python -m src.paper.place_order_alpaca --symbol QQQ --notional 100 --side buy
```

The expected output is a dry-run message. It must not submit an order by default.

## Backtesting Rules

- Always include buy-and-hold in reports.
- Track at least:
  - total return
  - max drawdown
  - Sharpe ratio
  - trade count
  - end value
- Test multiple periods when a strategy looks good.
- Avoid cherry-picking one market regime.
- Treat high return plus high drawdown as a risk warning, not an automatic win.

## Paper Trading Rules

- Paper mode is the only allowed order mode for now.
- `--execute` must still respect `TRADING_KILL_SWITCH`.
- Target allocation must be compared with current position before order submission.
- Every decision should be logged before the order call.
- Fail closed if data, account, or position reads fail.

## QuantConnect Prototypes

Files under `strategies/` are QuantConnect `main.py` prototypes. They are useful for UI experiments, but local harness work should live under `src/`.

When porting a QuantConnect strategy to local research:

1. Preserve the ticker, date range, and benchmark.
2. Reproduce buy-and-hold locally first.
3. Reproduce the strategy signal.
4. Compare key metrics with QuantConnect.
5. Record differences in `docs/experiment_log.md`.

## Do Not Do

- Do not add live trading by flipping a boolean.
- Do not hide safety checks behind convenience helpers.
- Do not create autonomous strategy search that can place orders.
- Do not store generated market data or reports in git unless the user explicitly asks.
- Do not remove user-created files or results without permission.
