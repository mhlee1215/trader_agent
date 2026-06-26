const HISTORY_KEY = "live_account_history";
const ALPACA_BASE_URL = "https://api.alpaca.markets";

export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);

    if (request.method === "OPTIONS") {
      return withCors(new Response(null, { status: 204 }));
    }

    if (url.pathname === "/api/health") {
      return json({
        ok: true,
        service: "trader-agent-api",
        now: new Date().toISOString()
      });
    }

    if (url.pathname === "/api/live-history" && request.method === "GET") {
      return json(await readHistory(env));
    }

    if (url.pathname === "/api/live-current" && request.method === "GET") {
      return json(await readLiveSnapshot(env));
    }

    if (url.pathname === "/api/snapshot" && request.method === "POST") {
      const unauthorized = unauthorizedResponse(request, env);
      if (unauthorized) return unauthorized;
      const snapshot = await appendLiveSnapshot(env);
      return json(snapshot);
    }

    return json({ error: "not_found" }, { status: 404 });
  },

  async scheduled(event, env, ctx) {
    ctx.waitUntil(appendLiveSnapshot(env));
  }
};

async function appendLiveSnapshot(env) {
  const snapshot = await readLiveSnapshot(env);
  const history = await readHistory(env);
  history.push(snapshot);
  await env.TRADER_AGENT_KV.put(HISTORY_KEY, JSON.stringify(history, null, 2));
  return snapshot;
}

async function readLiveSnapshot(env) {
  const [account, clock, positions, orders, contribution] = await Promise.all([
    alpacaGet(env, "/v2/account"),
    alpacaGet(env, "/v2/clock"),
    alpacaGet(env, "/v2/positions"),
    alpacaGet(env, "/v2/orders?status=open"),
    readContributedCash(env)
  ]);

  return {
    timestamp: new Date().toISOString(),
    account: "live",
    status: account.status,
    trading_blocked: Boolean(account.trading_blocked),
    account_blocked: Boolean(account.account_blocked),
    market_is_open: Boolean(clock.is_open),
    equity: toNumber(account.equity),
    cash: toNumber(account.cash),
    buying_power: toNumber(account.buying_power),
    live_capital_cap: toNumber(env.LIVE_CAPITAL_CAP || "100"),
    live_contributed_cash: contribution.amount,
    live_contributed_cash_source: contribution.source,
    open_orders: orders.map(order => ({
      symbol: order.symbol,
      side: String(order.side),
      status: String(order.status),
      notional: toNumber(order.notional),
      qty: toNumber(order.qty),
      filled_qty: toNumber(order.filled_qty)
    })),
    positions: positions.map(position => ({
      symbol: position.symbol,
      qty: toNumber(position.qty),
      market_value: toNumber(position.market_value),
      cost_basis: toNumber(position.cost_basis),
      unrealized_pl: toNumber(position.unrealized_pl),
      unrealized_plpc: toNumber(position.unrealized_plpc)
      }))
  };
}

async function readContributedCash(env) {
  const mode = String(env.LIVE_CONTRIBUTED_CASH_MODE || "auto").toLowerCase();
  const configured = toNumber(env.LIVE_CONTRIBUTED_CASH || env.LIVE_INITIAL_SEED || env.LIVE_CAPITAL_CAP || "100");

  if (mode === "manual") {
    return { amount: configured, source: "manual" };
  }

  try {
    const activities = await readCashActivities(env);
    const amount = activities.reduce((sum, activity) => sum + toNumber(activity.net_amount), 0);
    return {
      amount: amount > 0 ? amount : configured,
      source: amount > 0 ? "alpaca_activities_TRANS" : "configured_fallback"
    };
  } catch (error) {
    return { amount: configured, source: `configured_fallback:${error.message}` };
  }
}

async function readCashActivities(env) {
  const activities = [];
  let pageToken = "";

  for (let page = 0; page < 20; page += 1) {
    const params = new URLSearchParams({
      direction: "asc",
      page_size: "100"
    });
    if (pageToken) params.set("page_token", pageToken);

    const batch = await alpacaGet(env, `/v2/account/activities/TRANS?${params.toString()}`);
    if (!Array.isArray(batch) || batch.length === 0) break;

    activities.push(...batch);
    if (batch.length < 100) break;
    pageToken = batch[batch.length - 1].id;
  }

  return activities.filter(activity => ["CSD", "CSW", "TRANS"].includes(activity.activity_type));
}

async function readHistory(env) {
  const raw = await env.TRADER_AGENT_KV.get(HISTORY_KEY);
  if (!raw) return [];

  const parsed = JSON.parse(raw);
  if (!Array.isArray(parsed)) {
    throw new Error(`KV key ${HISTORY_KEY} must contain a JSON list`);
  }
  return parsed;
}

async function alpacaGet(env, path) {
  const response = await fetch(`${ALPACA_BASE_URL}${path}`, {
    headers: {
      "APCA-API-KEY-ID": env.ALPACA_LIVE_API_KEY,
      "APCA-API-SECRET-KEY": env.ALPACA_LIVE_SECRET_KEY
    }
  });

  if (!response.ok) {
    const body = await response.text();
    throw new Error(`Alpaca ${path} failed: HTTP ${response.status}: ${body}`);
  }

  return response.json();
}

function unauthorizedResponse(request, env) {
  if (!env.SNAPSHOT_ADMIN_TOKEN) return;

  const expected = `Bearer ${env.SNAPSHOT_ADMIN_TOKEN}`;
  if (request.headers.get("Authorization") !== expected) {
    return withCors(new Response("Unauthorized", { status: 401 }));
  }
}

function toNumber(value) {
  if (value === null || value === undefined || value === "") return 0;
  return Number(value);
}

function json(data, init = {}) {
  return withCors(new Response(JSON.stringify(data, null, 2), {
    ...init,
    headers: {
      "content-type": "application/json; charset=utf-8",
      ...(init.headers || {})
    }
  }));
}

function withCors(response) {
  const next = new Response(response.body, response);
  next.headers.set("access-control-allow-origin", "*");
  next.headers.set("access-control-allow-methods", "GET,POST,OPTIONS");
  next.headers.set("access-control-allow-headers", "authorization,content-type");
  return next;
}
