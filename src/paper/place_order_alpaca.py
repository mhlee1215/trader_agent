import argparse
from pathlib import Path

from src.common.alpaca_accounts import get_account_config, kill_switch_enabled, make_trading_client
from src.common.env import load_account_env


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Place or preview an Alpaca paper order.")
    parser.add_argument("--symbol", required=True)
    parser.add_argument("--notional", required=True, type=float)
    parser.add_argument("--side", choices=["buy", "sell"], required=True)
    parser.add_argument(
        "--env-file",
        type=Path,
        default=None,
        help="Optional paper env file. Defaults to .env.paper when present.",
    )
    parser.add_argument("--dry-run", action="store_true", default=True)
    parser.add_argument("--execute", action="store_true", help="Actually submit the paper order.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    dry_run = args.dry_run and not args.execute

    if dry_run:
        print(f"DRY RUN: {args.side.upper()} ${args.notional:.2f} of {args.symbol}")
        return

    try:
        env = load_account_env("paper", args.env_file)
    except RuntimeError as exc:
        raise SystemExit(str(exc)) from exc

    config = get_account_config("paper")
    if kill_switch_enabled(env, config):
        raise SystemExit(f"{config.kill_switch_name}=true. Refusing to submit paper order.")

    if env.get("TRADING_MODE", "paper") not in ["paper", "dual"]:
        raise SystemExit("This command only supports paper mode. Use TRADING_MODE=paper or TRADING_MODE=dual.")

    try:
        from alpaca.trading.enums import OrderSide, TimeInForce
        from alpaca.trading.requests import MarketOrderRequest
    except ImportError as exc:
        raise SystemExit("Install dependencies first: python3 -m pip install -r requirements.txt") from exc

    client = make_trading_client(env, config)
    order = MarketOrderRequest(
        symbol=args.symbol,
        notional=args.notional,
        side=OrderSide.BUY if args.side == "buy" else OrderSide.SELL,
        time_in_force=TimeInForce.DAY,
    )
    result = client.submit_order(order)
    print(result)


if __name__ == "__main__":
    main()
