import argparse
import json
from pathlib import Path

from src.common.paths import REPORTS_DIR, ensure_runtime_dirs
from src.strategies.sma import sma_cross_entries_exits, sma_partial_weights


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run a vectorbt SMA parameter sweep.")
    parser.add_argument("--config", default="configs/qqq_sma.json", type=Path)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    ensure_runtime_dirs()

    try:
        import pandas as pd
        import vectorbt as vbt
    except ImportError as exc:
        raise SystemExit("Install dependencies first: python3 -m pip install -r requirements.txt") from exc

    config = json.loads(args.config.read_text())
    data_path = Path(config["data_path"])
    prices = read_price_csv(data_path)
    close = prices["close"]

    rows: list[dict[str, object]] = []

    hold_pf = vbt.Portfolio.from_holding(
        close,
        init_cash=config["cash"],
        fees=config["fees"],
        freq="1D",
    )
    hold_row = metrics_row("buy_hold", None, None, "full", hold_pf)
    rows.append(hold_row)

    for fast in config["fast_windows"]:
        for slow in config["slow_windows"]:
            if fast >= slow:
                continue

            entries, exits = sma_cross_entries_exits(close, fast, slow)

            pf = vbt.Portfolio.from_signals(
                close,
                entries,
                exits,
                init_cash=config["cash"],
                fees=config["fees"],
                slippage=config["slippage"],
                freq="1D",
            )
            rows.append(metrics_row("sma_cross", fast, slow, "full", pf))

            weights = sma_partial_weights(
                close,
                fast,
                slow,
                uptrend_weight=config.get("uptrend_weight", 1.0),
                downtrend_weight=config.get("downtrend_weight", 0.5),
            )
            rebalance_weights = weights.where(weights.ne(weights.shift()))
            partial_pf = vbt.Portfolio.from_orders(
                close,
                size=rebalance_weights,
                size_type="targetpercent",
                init_cash=config["cash"],
                fees=config["fees"],
                slippage=config["slippage"],
                freq="1D",
            )
            rows.append(metrics_row("sma_partial", fast, slow, "partial", partial_pf))

    results = pd.DataFrame(rows)
    benchmark = results[results["strategy"] == "buy_hold"].iloc[0]
    results["excess_return_vs_bh_pct"] = results["total_return_pct"] - benchmark["total_return_pct"]
    results["drawdown_improvement_vs_bh_pct"] = benchmark["max_drawdown_pct"] - results["max_drawdown_pct"]
    results["sharpe_improvement_vs_bh"] = results["sharpe"] - benchmark["sharpe"]
    results["score"] = (
        results["cagr_pct"]
        - results["max_drawdown_pct"] * 0.5
        + results["sharpe"].fillna(0) * 10
        - results["trades"] * 0.02
    )
    results = results.sort_values(["score", "sharpe"], ascending=False)
    csv_path = REPORTS_DIR / f"{config['name']}_results.csv"
    md_path = REPORTS_DIR / f"{config['name']}_results.md"
    results.to_csv(csv_path, index=False)
    md_path.write_text(to_markdown_table(results.head(25)))

    print(results.head(10).to_string(index=False))
    print(f"Wrote {csv_path}")
    print(f"Wrote {md_path}")


def read_price_csv(path: Path):
    import pandas as pd

    prices = pd.read_csv(path)
    date_column = "timestamp" if "timestamp" in prices.columns else "Date"
    close_column = "close" if "close" in prices.columns else "Close"

    prices[date_column] = pd.to_datetime(prices[date_column])
    prices = prices.sort_values(date_column).set_index(date_column)
    return prices.rename(columns={close_column: "close"})[["close"]]


def metrics_row(name: str, fast: int | None, slow: int | None, exposure: str, portfolio) -> dict[str, object]:
    stats = portfolio.stats()
    value = portfolio.value()
    start_value = float(value.iloc[0])
    end_value = float(value.iloc[-1])
    years = max((value.index[-1] - value.index[0]).days / 365.25, 1 / 365.25)
    return {
        "strategy": name,
        "fast": fast,
        "slow": slow,
        "exposure": exposure,
        "total_return_pct": safe_float(stats, "Total Return [%]"),
        "cagr_pct": ((end_value / start_value) ** (1 / years) - 1) * 100,
        "max_drawdown_pct": safe_float(stats, "Max Drawdown [%]"),
        "sharpe": safe_float(stats, "Sharpe Ratio"),
        "sortino": safe_float(stats, "Sortino Ratio"),
        "calmar": safe_float(stats, "Calmar Ratio"),
        "trades": int(stats.get("Total Trades", 0)),
        "exposure_time_pct": exposure_time_pct(portfolio),
        "start": value.index[0].date().isoformat(),
        "end": value.index[-1].date().isoformat(),
        "end_value": end_value,
    }


def safe_float(stats, key: str) -> float:
    value = stats.get(key)
    try:
        return float(value)
    except (TypeError, ValueError):
        return float("nan")


def exposure_time_pct(portfolio) -> float:
    asset_value = portfolio.asset_value()
    value = portfolio.value()
    invested = asset_value.abs() > value.abs() * 0.01
    return float(invested.mean() * 100)


def to_markdown_table(frame) -> str:
    columns = list(frame.columns)
    lines = [
        "| " + " | ".join(columns) + " |",
        "| " + " | ".join(["---"] * len(columns)) + " |",
    ]

    for _, row in frame.iterrows():
        values = [format_markdown_value(row[column]) for column in columns]
        lines.append("| " + " | ".join(values) + " |")

    return "\n".join(lines) + "\n"


def format_markdown_value(value) -> str:
    if isinstance(value, float):
        return f"{value:.4f}"
    if value is None:
        return ""
    return str(value)


if __name__ == "__main__":
    main()
