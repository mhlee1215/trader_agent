import argparse
from pathlib import Path

from src.common.alpaca_accounts import get_account_config, make_trading_client
from src.common.env import account_env_sources, load_account_env


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Read Alpaca paper/live account status without submitting orders.")
    parser.add_argument("--account", choices=["paper", "live"], required=True)
    parser.add_argument(
        "--env-file",
        type=Path,
        default=None,
        help="Optional account-specific env file. Defaults to .env.paper or .env.live when present.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    try:
        env = load_account_env(args.account, args.env_file)
    except RuntimeError as exc:
        raise SystemExit(str(exc)) from exc

    config = get_account_config(args.account)
    try:
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

    print(f"account={args.account}")
    print(f"env_sources={', '.join(account_env_sources(args.account, args.env_file)) or 'none'}")
    print(f"status={account.status}")
    print(f"trading_blocked={account.trading_blocked}")
    print(f"account_blocked={account.account_blocked}")
    print(f"equity={account.equity}")
    print(f"cash={account.cash}")
    print(f"buying_power={account.buying_power}")
    print(f"market_is_open={clock.is_open}")
    print(f"next_open={clock.next_open}")
    print(f"next_close={clock.next_close}")
    print(f"open_orders={len(orders)}")
    for order in orders:
        print(
            f"ORDER {order.symbol} {order.side} {order.status} "
            f"notional={order.notional} qty={order.qty} filled_qty={order.filled_qty}"
        )
    print(f"positions={len(positions)}")
    for position in positions:
        print(
            f"POSITION {position.symbol} qty={position.qty} "
            f"market_value={position.market_value} unrealized_pl={position.unrealized_pl}"
        )


if __name__ == "__main__":
    main()
