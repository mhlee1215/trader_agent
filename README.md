# Trader Agent

Beginner-safe trading research and operations harness.

Core stack:

```text
vectorbt       local research/backtesting
alpaca-py     Alpaca data, paper trading, and live account access
Cloudflare    deployed live dashboard API and static UI
```

This repository is not financial advice and is not a general-purpose live-trading system.

## Local Dashboard

```bash
npm install
npm run dev:dashboard
```

Open:

```text
http://127.0.0.1:8765/live_dashboard.html
```

Local dashboard data comes from:

```text
reports/live_account_history.json
```

Generate a live snapshot locally:

```bash
.venv/bin/python -m src.trading.snapshot_account --account live
```

## Cloudflare

Deployment docs:

```text
docs/cloudflare_deploy.md
```

Main pieces:

```text
public/live_dashboard.html   Cloudflare Pages static dashboard
worker/src/index.js          Worker API + scheduled Alpaca snapshot
Cloudflare KV                live_account_history storage
```

## Safety

- Never commit `.env`, `.env.live`, `.env.paper`, or `.dev.vars`.
- Never put Alpaca secrets in browser-side JavaScript.
- Live account automation is capped by `LIVE_CAPITAL_CAP`.
- Generated market data and runtime reports are ignored by git.
