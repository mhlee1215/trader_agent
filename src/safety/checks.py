from src.common.env import load_env


def kill_switch_enabled() -> bool:
    env = load_env()
    return env.get("TRADING_KILL_SWITCH", "true").lower() == "true"


def assert_paper_mode() -> None:
    env = load_env()
    if env.get("TRADING_MODE", "paper") != "paper":
        raise RuntimeError("Only paper mode is allowed in the current harness.")
