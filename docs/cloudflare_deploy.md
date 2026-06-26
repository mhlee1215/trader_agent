# Cloudflare Deploy

This repo can run the dashboard locally and deploy it to Cloudflare Pages + Worker + KV.

Current deployments:

```text
Dashboard: https://trader-agent.pages.dev/
Worker API: https://trader-agent-api.minhaenl.workers.dev
```

## Architecture

```text
Cloudflare Pages
  public/live_dashboard.html

Cloudflare Worker
  worker/src/index.js
  GET /api/live-history
  GET /api/live-current
  POST /api/snapshot
  scheduled weekly snapshot

Cloudflare KV
  key: live_account_history
```

The browser never receives Alpaca API keys.

## Local

```bash
npm install
npm run dev:dashboard
```

Open:

```text
http://127.0.0.1:8765/live_dashboard.html
```

The local dev server serves:

```text
GET /api/live-history -> reports/live_account_history.json
```

In production, the dashboard calls:

```text
GET /api/live-current
```

on every page refresh, so the visible account metrics come directly from Alpaca through the Worker without exposing Alpaca keys to the browser. `GET /api/live-history` remains the stored trend history.

## Cloudflare Setup

Create a KV namespace:

```bash
npx wrangler kv namespace create TRADER_AGENT_KV
```

Put the returned namespace id into:

```text
worker/wrangler.jsonc
```

Set Worker secrets:

```bash
npx wrangler secret put ALPACA_LIVE_API_KEY --config worker/wrangler.jsonc
npx wrangler secret put ALPACA_LIVE_SECRET_KEY --config worker/wrangler.jsonc
npx wrangler secret put SNAPSHOT_ADMIN_TOKEN --config worker/wrangler.jsonc
```

Deploy Worker:

```bash
npm run deploy:worker
```

Deploy Pages:

```bash
npm run deploy:pages
```

For same-origin dashboard API calls, route `/api/*` on the dashboard domain to the Worker, or set `window.TRADER_AGENT_API_BASE` before loading the dashboard.

The current `public/live_dashboard.html` defaults to:

```text
https://trader-agent-api.minhaenl.workers.dev
```

Localhost still uses the local `/api/live-history` endpoint.

## Manual Snapshot

```bash
curl -X POST https://YOUR_WORKER_DOMAIN/api/snapshot \
  -H "Authorization: Bearer YOUR_SNAPSHOT_ADMIN_TOKEN"
```

## Schedule

The Worker snapshot cron is configured as:

```text
15 21 * * MON-FRI
```

This stores a fresh dashboard snapshot at 21:15 UTC on weekdays. It does not submit trades. The live trading automation remains weekly.
