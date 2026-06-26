import argparse
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from src.common.alpaca_accounts import (
    get_account_config,
    kill_switch_enabled,
    make_trading_client,
    max_order_notional,
    max_total_notional,
)
from src.common.env import account_env_sources, load_account_env
from src.common.paths import DATA_DIR


DEFAULT_UNIVERSE = Path("configs/broad_universe_symbols.txt")
STOCK_START = "AAPL"


@dataclass(frozen=True)
class Target:
    symbol: str
    weight: float
    score: float


@dataclass(frozen=True)
class PlannedOrder:
    symbol: str
    side: str
    notional: float
    current_value: float
    target_value: float


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Plan or submit Alpaca paper/live rebalance for large-cap momentum.")
    parser.add_argument("--account", choices=["paper", "live"], default="paper")
    parser.add_argument("--universe", default=DEFAULT_UNIVERSE, type=Path)
    parser.add_argument("--lookback", default=63, type=int)
    parser.add_argument("--top-n", default=5, type=int)
    parser.add_argument("--rebalance-frequency", choices=["M", "Q"], default="Q")
    parser.add_argument("--cash-buffer", default=0.02, type=float)
    parser.add_argument("--min-notional", default=5.0, type=float)
    parser.add_argument(
        "--env-file",
        type=Path,
        default=None,
        help="Optional account-specific env file. Defaults to .env.paper or .env.live when present.",
    )
    parser.add_argument("--execute", action="store_true", help="Submit orders. Blocked by account-specific kill switch.")
    parser.add_argument(
        "--auto-live-rebalance",
        action="store_true",
        help="Allow scheduled live execution when LIVE_AUTO_REBALANCE=true. Use only for approved automation.",
    )
    parser.add_argument(
        "--confirm-live-submit",
        default="",
        help="Required exact value 'I_APPROVE_LIVE_ORDER' before manual live order submission.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    try:
        env = load_account_env(args.account, args.env_file)
    except RuntimeError as exc:
        raise SystemExit(str(exc)) from exc

    config = get_account_config(args.account)
    assert_account_env(env, args.account)

    try:
        import alpaca.trading.client  # noqa: F401
    except ImportError as exc:
        raise SystemExit("Install dependencies first: .venv/bin/python -m pip install -r requirements.txt") from exc

    try:
        client = make_trading_client(env, config)
    except RuntimeError as exc:
        raise SystemExit(str(exc)) from exc

    stock_symbols = load_stock_symbols(args.universe)
    close = load_close_matrix(stock_symbols)
    rebalance_date = latest_rebalance_date(close.index, args.rebalance_frequency)
    targets = latest_top_momentum_targets(close, rebalance_date, args.lookback, args.top_n)

    print(f"strategy=Quarterly Large-Cap Top-{args.top_n} Momentum {args.lookback}D")
    print(f"data_end={close.index.max().date().isoformat()}")
    print(f"rebalance_date={rebalance_date.date().isoformat()}")
    print("targets:")
    for target in targets:
        print(f"  {target.symbol}: weight={target.weight:.2%} momentum={target.score:.2%}")

    try:
        account = client.get_account()
        clock = client.get_clock()
        open_orders = client.get_orders()
        positions = client.get_all_positions()
    except Exception as exc:
        raise SystemExit(f"Failed to read {args.account} Alpaca account. Refusing to rebalance: {exc}") from exc
    equity = float(account.equity)
    capital_cap = live_capital_cap(env, args.account, equity)
    deployable_equity = capital_cap * (1.0 - args.cash_buffer)

    print(f"account={args.account}")
    print(f"env_sources={', '.join(account_env_sources(args.account, args.env_file)) or 'none'}")
    print(f"account_status={account.status}")
    print(f"trading_blocked={account.trading_blocked}")
    print(f"account_blocked={account.account_blocked}")
    print(f"market_is_open={clock.is_open}")
    print(f"open_orders={len(open_orders)}")
    print(f"equity={equity:.2f}")
    print(f"capital_cap={capital_cap:.2f}")
    print(f"deployable_equity={deployable_equity:.2f}")

    planned_orders = plan_orders(targets, positions, deployable_equity, args.min_notional)
    enforce_safety_limits(planned_orders, env, config, equity)
    enforce_no_duplicate_orders(planned_orders, open_orders, args.account)
    if not planned_orders:
        print("planned_orders=none")
        return

    print("planned_orders:")
    for order in planned_orders:
        print(
            f"  {order.side.upper()} {order.symbol} ${order.notional:.2f} "
            f"current=${order.current_value:.2f} target=${order.target_value:.2f}"
        )

    if not args.execute:
        print(f"DRY RUN: no orders submitted. Pass --execute to submit {args.account} orders.")
        return

    if kill_switch_enabled(env, config):
        raise SystemExit(f"{config.kill_switch_name}=true. Refusing to submit {args.account} orders.")

    if args.account == "live" and not live_submission_allowed(env, args):
        raise SystemExit(
            "Live submission requires manual --confirm-live-submit I_APPROVE_LIVE_ORDER "
            "or scheduled --auto-live-rebalance with LIVE_AUTO_REBALANCE=true."
        )

    if args.account == "live" and (account.trading_blocked or account.account_blocked):
        raise SystemExit("Live account is blocked. Refusing to submit orders.")

    if not clock.is_open:
        raise SystemExit(f"Market is not open. Refusing to submit {args.account} orders.")

    submit_orders(client, planned_orders)


def load_stock_symbols(path: Path) -> list[str]:
    symbols = [line.strip() for line in path.read_text().splitlines() if line.strip()]
    if STOCK_START not in symbols:
        raise SystemExit(f"{path} does not contain expected stock marker {STOCK_START}.")
    return symbols[symbols.index(STOCK_START) :]


def load_close_matrix(symbols: list[str]) -> pd.DataFrame:
    frames = {}
    for symbol in symbols:
        path = DATA_DIR / f"{symbol}_daily.csv"
        if not path.exists():
            continue
        frame = pd.read_csv(path, parse_dates=["timestamp"])
        frames[symbol] = frame.sort_values("timestamp").set_index("timestamp")["close"].astype(float)

    if not frames:
        raise SystemExit("No stock data found. Fetch Alpaca bars first.")

    return pd.DataFrame(frames).dropna().sort_index()


def latest_rebalance_date(index: pd.Index, frequency: str) -> pd.Timestamp:
    plain_index = index.tz_convert(None) if getattr(index, "tz", None) is not None else index
    periods = plain_index.to_period("Q" if frequency == "Q" else "M")
    first_dates = pd.Series(index, index=index).groupby(periods).first()
    return pd.Timestamp(first_dates.iloc[-1])


def latest_top_momentum_targets(close: pd.DataFrame, rebalance_date: pd.Timestamp, lookback: int, top_n: int) -> list[Target]:
    momentum = close.pct_change(lookback)
    if rebalance_date not in momentum.index:
        rebalance_date = momentum.index[momentum.index.get_indexer([rebalance_date], method="pad")[0]]
    scores = momentum.loc[rebalance_date].dropna().sort_values(ascending=False)
    selected = [(symbol, score) for symbol, score in scores.items() if score > 0][:top_n]
    if not selected:
        return [Target("SHY", 1.0, 0.0)]
    weight = 1.0 / len(selected)
    return [Target(symbol, weight, float(score)) for symbol, score in selected]


def assert_account_env(env: dict[str, str], account: str) -> None:
    if account == "paper":
        mode = env.get("TRADING_MODE", "paper")
        if mode not in ["paper", "dual"]:
            raise SystemExit("Paper account requires TRADING_MODE=paper or TRADING_MODE=dual.")
    else:
        mode = env.get("TRADING_MODE", "")
        if mode not in ["live", "dual"]:
            raise SystemExit("Live account requires TRADING_MODE=live or TRADING_MODE=dual.")


def live_capital_cap(env: dict[str, str], account: str, equity: float) -> float:
    if account != "live":
        return equity

    initial_seed = float(env.get("LIVE_INITIAL_SEED", "100"))
    seed_plus_profit = initial_seed + max(0.0, equity - initial_seed)
    explicit_cap = float(env.get("LIVE_CAPITAL_CAP", seed_plus_profit))
    return min(equity, seed_plus_profit, explicit_cap)


def live_submission_allowed(env: dict[str, str], args: argparse.Namespace) -> bool:
    if args.confirm_live_submit == "I_APPROVE_LIVE_ORDER":
        return True

    auto_enabled = env.get("LIVE_AUTO_REBALANCE", "false").lower() == "true"
    return args.auto_live_rebalance and auto_enabled


def plan_orders(targets, positions, deployable_equity: float, min_notional: float) -> list[PlannedOrder]:
    current_values = {position.symbol: float(position.market_value) for position in positions}
    target_values = {target.symbol: deployable_equity * target.weight for target in targets}
    symbols = sorted(set(current_values) | set(target_values))

    planned: list[PlannedOrder] = []
    for symbol in symbols:
        current_value = current_values.get(symbol, 0.0)
        target_value = target_values.get(symbol, 0.0)
        difference = target_value - current_value
        if abs(difference) < min_notional:
            continue
        side = "buy" if difference > 0 else "sell"
        notional = abs(difference)
        if side == "sell":
            notional = min(notional, current_value)
        planned.append(
            PlannedOrder(
                symbol=symbol,
                side=side,
                notional=notional,
                current_value=current_value,
                target_value=target_value,
            )
        )

    return sorted(planned, key=lambda order: 0 if order.side == "sell" else 1)


def enforce_safety_limits(planned_orders: list[PlannedOrder], env: dict[str, str], config, equity: float) -> None:
    max_single = max_order_notional(env, config)
    max_total = effective_max_total_notional(env, config, equity)
    total = sum(order.notional for order in planned_orders)

    if total > max_total:
        raise SystemExit(
            f"Planned total ${total:.2f} exceeds {config.max_total_notional_name}=${max_total:.2f}."
        )

    for order in planned_orders:
        if order.notional > max_single:
            raise SystemExit(
                f"{order.symbol} order ${order.notional:.2f} exceeds "
                f"{config.max_order_notional_name}=${max_single:.2f}."
            )


def effective_max_total_notional(env: dict[str, str], config, equity: float) -> float:
    max_total = max_total_notional(env, config)
    if config.name != "live":
        return max_total

    initial_seed = float(env.get("LIVE_INITIAL_SEED", "100"))
    profit = max(0.0, equity - initial_seed)
    return max_total + profit


def enforce_no_duplicate_orders(planned_orders: list[PlannedOrder], open_orders, account: str) -> None:
    open_symbols = {order.symbol for order in open_orders}
    duplicate_symbols = sorted({order.symbol for order in planned_orders} & open_symbols)
    if duplicate_symbols:
        raise SystemExit(
            f"{account} account already has open orders for {', '.join(duplicate_symbols)}. "
            "Refusing to create duplicate orders."
        )


def submit_orders(client, planned_orders: list[PlannedOrder]) -> None:
    from alpaca.trading.enums import OrderSide, TimeInForce
    from alpaca.trading.requests import MarketOrderRequest

    for order in planned_orders:
        request = MarketOrderRequest(
            symbol=order.symbol,
            notional=round(order.notional, 2),
            side=OrderSide.BUY if order.side == "buy" else OrderSide.SELL,
            time_in_force=TimeInForce.DAY,
        )
        result = client.submit_order(request)
        print(f"submitted {order.side} {order.symbol} ${order.notional:.2f}: {result.id}")


if __name__ == "__main__":
    main()
