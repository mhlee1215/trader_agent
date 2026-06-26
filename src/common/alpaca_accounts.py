from dataclasses import dataclass

from src.common.env import require_env


@dataclass(frozen=True)
class AlpacaAccountConfig:
    name: str
    paper: bool
    api_key_name: str
    secret_key_name: str
    kill_switch_name: str
    max_order_notional_name: str
    max_total_notional_name: str


ACCOUNT_CONFIGS = {
    "paper": AlpacaAccountConfig(
        name="paper",
        paper=True,
        api_key_name="ALPACA_PAPER_API_KEY",
        secret_key_name="ALPACA_PAPER_SECRET_KEY",
        kill_switch_name="PAPER_TRADING_KILL_SWITCH",
        max_order_notional_name="PAPER_MAX_ORDER_NOTIONAL",
        max_total_notional_name="PAPER_MAX_TOTAL_NOTIONAL",
    ),
    "live": AlpacaAccountConfig(
        name="live",
        paper=False,
        api_key_name="ALPACA_LIVE_API_KEY",
        secret_key_name="ALPACA_LIVE_SECRET_KEY",
        kill_switch_name="LIVE_TRADING_KILL_SWITCH",
        max_order_notional_name="LIVE_MAX_ORDER_NOTIONAL",
        max_total_notional_name="LIVE_MAX_TOTAL_NOTIONAL",
    ),
}


def get_account_config(account: str) -> AlpacaAccountConfig:
    try:
        return ACCOUNT_CONFIGS[account]
    except KeyError as exc:
        raise ValueError(f"Unsupported account: {account}") from exc


def account_credentials(env: dict[str, str], config: AlpacaAccountConfig) -> tuple[str, str]:
    if config.name == "paper":
        api_key = env.get(config.api_key_name) or env.get("ALPACA_API_KEY")
        secret_key = env.get(config.secret_key_name) or env.get("ALPACA_SECRET_KEY")
        if not api_key:
            require_env(env, config.api_key_name)
        if not secret_key:
            require_env(env, config.secret_key_name)
        return str(api_key), str(secret_key)

    return require_env(env, config.api_key_name), require_env(env, config.secret_key_name)


def kill_switch_enabled(env: dict[str, str], config: AlpacaAccountConfig) -> bool:
    default = env.get("TRADING_KILL_SWITCH", "true") if config.name == "paper" else "true"
    return env.get(config.kill_switch_name, default).lower() == "true"


def max_order_notional(env: dict[str, str], config: AlpacaAccountConfig) -> float:
    default = "25000" if config.name == "paper" else "25"
    return float(env.get(config.max_order_notional_name, default))


def max_total_notional(env: dict[str, str], config: AlpacaAccountConfig) -> float:
    default = "100000" if config.name == "paper" else "25"
    return float(env.get(config.max_total_notional_name, default))


def make_trading_client(env: dict[str, str], config: AlpacaAccountConfig):
    from alpaca.trading.client import TradingClient

    api_key, secret_key = account_credentials(env, config)
    return TradingClient(api_key, secret_key, paper=config.paper)
