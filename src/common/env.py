from pathlib import Path


def load_env(path: Path = Path(".env")) -> dict[str, str]:
    values: dict[str, str] = {}

    if not path.exists():
        return values

    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        values[key.strip()] = value.strip().strip('"').strip("'")

    return values


def load_account_env(account: str, env_file: Path | None = None) -> dict[str, str]:
    """Load common env first, then account-specific overrides.

    Defaults:
    - .env
    - .env.paper or .env.live when that file exists

    If env_file is provided, it is loaded after .env instead of the default
    account-specific path. Later files override earlier values.
    """
    values = load_env(Path(".env"))
    if env_file is not None and not env_file.exists():
        raise RuntimeError(f"Account env file does not exist: {env_file}")

    account_path = env_file or Path(f".env.{account}")
    if account_path.exists():
        account_values = load_env(account_path)
        account_values = normalize_account_keys(account, account_values)
        values.update(account_values)
    return values


def normalize_account_keys(account: str, values: dict[str, str]) -> dict[str, str]:
    normalized = dict(values)
    prefix = account.upper()

    generic_key = normalized.get("ALPACA_API_KEY")
    generic_secret = normalized.get("ALPACA_SECRET_KEY")
    account_key_name = f"ALPACA_{prefix}_API_KEY"
    account_secret_name = f"ALPACA_{prefix}_SECRET_KEY"

    if generic_key and not normalized.get(account_key_name):
        normalized[account_key_name] = generic_key
    if generic_secret and not normalized.get(account_secret_name):
        normalized[account_secret_name] = generic_secret

    return normalized


def account_env_sources(account: str, env_file: Path | None = None) -> list[str]:
    sources = []
    base_path = Path(".env")
    if base_path.exists():
        sources.append(str(base_path))

    account_path = env_file or Path(f".env.{account}")
    if env_file is not None or account_path.exists():
        sources.append(str(account_path))

    return sources


def require_env(values: dict[str, str], key: str) -> str:
    value = values.get(key)
    if not value:
        raise RuntimeError(f"Missing required environment value: {key}")

    return value
