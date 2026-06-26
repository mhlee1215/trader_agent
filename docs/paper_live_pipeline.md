# Paper and Live Account Pipelines

This repo now separates Alpaca paper and live account operations.

## Account Separation

| Pipeline | Purpose | Default Order Behavior |
| --- | --- | --- |
| Paper | Strategy rehearsal, paper positions, daily dry-runs | Dry-run unless `--execute` and paper kill switch is off |
| Live | Tiny real-money transaction tests only | Dry-run unless `--execute`, live kill switch is off, market is open, limits pass, and manual confirmation or approved automation flag is present |

## Environment Variables

The loader reads `.env` first, then an account-specific override if it exists:

```text
.env
.env.paper
.env.live
```

For cleaner operations, keep shared/default settings in `.env`, paper credentials in `.env.paper`, and live credentials in `.env.live`. The real `.env*` files are ignored by git; only example files should be committed.

Inside `.env.paper` or `.env.live`, either account-specific names or the generic Alpaca names are accepted. For example, `.env.live` may use either `ALPACA_LIVE_API_KEY` / `ALPACA_LIVE_SECRET_KEY` or `ALPACA_API_KEY` / `ALPACA_SECRET_KEY`. Generic names from the shared `.env` file are not used for live credentials.

Paper can still use the old keys:

```text
ALPACA_API_KEY
ALPACA_SECRET_KEY
```

New setup should prefer:

```text
ALPACA_PAPER_API_KEY
ALPACA_PAPER_SECRET_KEY
PAPER_TRADING_KILL_SWITCH=true
PAPER_MAX_ORDER_NOTIONAL=25000
PAPER_MAX_TOTAL_NOTIONAL=100000
```

Live uses separate keys and separate safety limits:

```text
ALPACA_LIVE_API_KEY
ALPACA_LIVE_SECRET_KEY
LIVE_TRADING_KILL_SWITCH=true
LIVE_MAX_ORDER_NOTIONAL=25
LIVE_MAX_TOTAL_NOTIONAL=25
LIVE_INITIAL_SEED=100
LIVE_CAPITAL_CAP=100
LIVE_AUTO_REBALANCE=false
```

Use `TRADING_MODE=dual` only when both paper and live pipelines are intentionally enabled for read-only checks and dry-runs.

You can also pass an explicit account env file:

```bash
.venv/bin/python -m src.trading.account_status --account live --env-file .env.live
```

## Read-Only Account Checks

Paper:

```bash
.venv/bin/python -m src.trading.account_status --account paper
```

Live:

```bash
.venv/bin/python -m src.trading.account_status --account live
```

These commands do not submit orders.

## Live Dashboard

Save a live account snapshot:

```bash
.venv/bin/python -m src.trading.snapshot_account --account live
```

Open or embed the HTML dashboard:

```text
reports/live_dashboard.html
```

The dashboard is plain HTML/CSS/JavaScript and reads:

```text
reports/live_account_history.json
```

Do not put Alpaca API keys in browser-side JavaScript. Account data collection stays in the Python snapshot command.

## Daily Automation Policy

- Paper automation is allowed to execute the paper rebalance once per trading day after the market opens.
- Live automation is allowed to execute once per week, Monday after the market opens, only when `LIVE_AUTO_REBALANCE=true`.
- Live deployment is capped by account equity and `LIVE_CAPITAL_CAP`; keep `LIVE_CAPITAL_CAP=100` for the initial live-money experiment unless intentionally changed.
- Both paper and live execution commands refuse to submit orders when Alpaca reports the market is closed.

## Rebalance Dry-Runs

Paper dry-run:

```bash
.venv/bin/python -m src.paper.rebalance_large_cap_momentum --account paper
```

Live dry-run:

```bash
.venv/bin/python -m src.paper.rebalance_large_cap_momentum --account live
```

## Paper Execution

Paper execution requires:

- `TRADING_MODE=paper` or `TRADING_MODE=dual`
- `PAPER_TRADING_KILL_SWITCH=false` or old `TRADING_KILL_SWITCH=false`
- Planned orders below `PAPER_MAX_ORDER_NOTIONAL`
- Planned total below `PAPER_MAX_TOTAL_NOTIONAL`
- No duplicate open orders for the same planned symbols

Command:

```bash
.venv/bin/python -m src.paper.rebalance_large_cap_momentum --account paper --execute
```

## Live Execution

Live execution requires all of the following:

- `TRADING_MODE=live` or `TRADING_MODE=dual`
- `LIVE_TRADING_KILL_SWITCH=false`
- Live API credentials in `ALPACA_LIVE_API_KEY` and `ALPACA_LIVE_SECRET_KEY`
- Market is open
- Account is not blocked
- Planned orders below `LIVE_MAX_ORDER_NOTIONAL`
- Planned total below `LIVE_MAX_TOTAL_NOTIONAL`
- No duplicate open orders for the same planned symbols
- Manual explicit confirmation flag:

```text
--confirm-live-submit I_APPROVE_LIVE_ORDER
```

Scheduled live automation instead requires:

```text
LIVE_AUTO_REBALANCE=true
LIVE_CAPITAL_CAP=100
--auto-live-rebalance
```

Command shape:

```bash
.venv/bin/python -m src.paper.rebalance_large_cap_momentum \
  --account live \
  --execute \
  --confirm-live-submit I_APPROVE_LIVE_ORDER
```

Scheduled command shape:

```bash
.venv/bin/python -m src.paper.rebalance_large_cap_momentum \
  --account live \
  --execute \
  --auto-live-rebalance
```
