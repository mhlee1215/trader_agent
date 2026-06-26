import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.common.alpaca_accounts import get_account_config, make_trading_client
from src.common.env import load_account_env
from src.common.paths import REPORTS_DIR, ensure_runtime_dirs


DEFAULT_OUTPUT = REPORTS_DIR / "live_account_history.json"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Save an Alpaca account snapshot for dashboard rendering.")
    parser.add_argument("--account", choices=["paper", "live"], default="live")
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help="JSON history file to append. Defaults to reports/live_account_history.json.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    ensure_runtime_dirs()

    try:
        env = load_account_env(args.account)
        config = get_account_config(args.account)
        client = make_trading_client(env, config)
    except RuntimeError as exc:
        raise SystemExit(str(exc)) from exc

    try:
        account = client.get_account()
        clock = client.get_clock()
        positions = client.get_all_positions()
        orders = client.get_orders()
    except Exception as exc:
        raise SystemExit(f"Failed to read {args.account} Alpaca account: {exc}") from exc

    snapshot = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "account": args.account,
        "status": str(account.status),
        "trading_blocked": bool(account.trading_blocked),
        "account_blocked": bool(account.account_blocked),
        "market_is_open": bool(clock.is_open),
        "equity": to_float(account.equity),
        "cash": to_float(account.cash),
        "buying_power": to_float(account.buying_power),
        "live_capital_cap": to_float(env.get("LIVE_CAPITAL_CAP")) if args.account == "live" else None,
        "open_orders": [
            {
                "symbol": order.symbol,
                "side": str(order.side),
                "status": str(order.status),
                "notional": to_float(order.notional),
                "qty": to_float(order.qty),
                "filled_qty": to_float(order.filled_qty),
            }
            for order in orders
        ],
        "positions": [
            {
                "symbol": position.symbol,
                "qty": to_float(position.qty),
                "market_value": to_float(position.market_value),
                "cost_basis": to_float(position.cost_basis),
                "unrealized_pl": to_float(position.unrealized_pl),
                "unrealized_plpc": to_float(position.unrealized_plpc),
            }
            for position in positions
        ],
    }

    history = load_history(args.output)
    history.append(snapshot)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(history, indent=2, sort_keys=True), encoding="utf-8")

    print(f"saved_snapshot={args.output}")
    print(f"account={args.account}")
    print(f"timestamp={snapshot['timestamp']}")
    print(f"equity={snapshot['equity']:.2f}")
    print(f"cash={snapshot['cash']:.2f}")
    print(f"positions={len(snapshot['positions'])}")
    print(f"open_orders={len(snapshot['open_orders'])}")


def load_history(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    try:
        loaded = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Invalid snapshot history JSON: {path}: {exc}") from exc
    if not isinstance(loaded, list):
        raise SystemExit(f"Snapshot history must be a JSON list: {path}")
    return loaded


def to_float(value) -> float:
    if value is None:
        return 0.0
    return float(value)


if __name__ == "__main__":
    main()
