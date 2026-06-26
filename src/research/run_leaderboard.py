import argparse
import html
import json
from dataclasses import dataclass
from pathlib import Path
from textwrap import dedent

import numpy as np
import pandas as pd

from src.common.paths import DATA_DIR, REPORTS_DIR, ensure_runtime_dirs
from src.strategies.sma import sma_cross_entries_exits, sma_partial_weights

CORE_SYMBOLS = [
    "SPY",
    "QQQ",
    "IWM",
    "EFA",
    "EEM",
    "IEF",
    "TLT",
    "AGG",
    "GLD",
    "DBC",
    "UUP",
    "SHY",
    "QLD",
    "TQQQ",
    "MTUM",
    "VLUE",
    "QUAL",
    "USMV",
]

SECTOR_ETFS = ["XLK", "XLY", "XLC", "XLF", "XLV", "XLI", "XLP", "XLE", "XLU", "XLB", "XLRE"]

LARGE_CAP_STOCKS = [
    "AAPL",
    "MSFT",
    "NVDA",
    "AMZN",
    "META",
    "GOOGL",
    "GOOG",
    "AVGO",
    "TSLA",
    "COST",
    "NFLX",
    "AMD",
    "ADBE",
    "CRM",
    "ORCL",
    "CSCO",
    "INTC",
    "IBM",
    "QCOM",
    "TXN",
    "AMAT",
    "MU",
    "LRCX",
    "JPM",
    "BAC",
    "GS",
    "MS",
    "V",
    "MA",
    "UNH",
    "LLY",
    "JNJ",
    "MRK",
    "ABBV",
    "PFE",
    "HD",
    "MCD",
    "NKE",
    "WMT",
    "TGT",
    "PG",
    "KO",
    "PEP",
    "XOM",
    "CVX",
    "CAT",
    "GE",
    "BA",
]


@dataclass
class StrategyResult:
    id: str
    name: str
    family: str
    description: str
    source_code: str
    metrics: dict[str, float | int | str | bool]
    equity_curve: pd.Series


@dataclass(frozen=True)
class CostModel:
    fee_rate: float
    slippage: float
    fixed_fee: float


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run strategy research and build an HTML leaderboard.")
    parser.add_argument("--cash", default=3000.0, type=float)
    parser.add_argument("--benchmark", default="QQQ")
    parser.add_argument("--output-name", default="strategy_leaderboard")
    parser.add_argument("--fee-rate", default=0.0001, type=float)
    parser.add_argument("--slippage", default=0.0005, type=float)
    parser.add_argument("--fixed-fee", default=0.25, type=float)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    ensure_runtime_dirs()

    try:
        import vectorbt as vbt
    except ImportError as exc:
        raise SystemExit("Install dependencies first: .venv/bin/python -m pip install -r requirements.txt") from exc

    prices = load_price_matrix(CORE_SYMBOLS + SECTOR_ETFS + LARGE_CAP_STOCKS)
    close = prices.sort_index()
    costs = CostModel(fee_rate=args.fee_rate, slippage=args.slippage, fixed_fee=args.fixed_fee)
    results = build_strategy_results(close, args.cash, args.benchmark, vbt, costs)

    benchmark = next(result for result in results if result.id == f"buy_hold_{args.benchmark.lower()}")
    for result in results:
        apply_relative_metrics(result, benchmark)

    rows = pd.DataFrame([flatten_result(result) for result in results])
    benchmark_score = float(rows.loc[rows["id"].eq(f"buy_hold_{args.benchmark.lower()}"), "score"].iloc[0])
    rows["beats_bh_score"] = rows["score"] > benchmark_score
    rows = rows.sort_values(["score", "total_return_pct"], ascending=False).reset_index(drop=True)
    rows.insert(0, "rank", range(1, len(rows) + 1))

    csv_path = REPORTS_DIR / f"{args.output_name}.csv"
    json_path = REPORTS_DIR / f"{args.output_name}.json"
    html_path = REPORTS_DIR / f"{args.output_name}.html"

    rows.to_csv(csv_path, index=False)
    json_path.write_text(json.dumps(leaderboard_payload(rows, results), indent=2))
    html_path.write_text(render_html(json.loads(json_path.read_text())))

    print(rows.head(15).to_string(index=False))
    print(f"Wrote {csv_path}")
    print(f"Wrote {json_path}")
    print(f"Wrote {html_path}")


def load_price_matrix(symbols: list[str]) -> pd.DataFrame:
    frames = {}
    for symbol in symbols:
        path = DATA_DIR / f"{symbol}_daily.csv"
        if not path.exists():
            continue
        frame = pd.read_csv(path, parse_dates=["timestamp"])
        frames[symbol] = frame.sort_values("timestamp").set_index("timestamp")["close"].astype(float)

    if not frames:
        raise SystemExit("No cached price data found. Run src.data.fetch_alpaca first.")

    return pd.DataFrame(frames).sort_index()


def build_strategy_results(close: pd.DataFrame, cash: float, benchmark_symbol: str, vbt, costs: CostModel) -> list[StrategyResult]:
    results: list[StrategyResult] = []
    benchmark_close = close[benchmark_symbol]

    results.append(
        run_holding_strategy(
            close=benchmark_close,
            cash=cash,
            vbt=vbt,
            costs=costs,
            strategy_id=f"buy_hold_{benchmark_symbol.lower()}",
            name=f"Buy & Hold {benchmark_symbol}",
            family="benchmark",
            description=f"Hold {benchmark_symbol} at 100% allocation for the whole test.",
            source_code=f"target_weight[{benchmark_symbol}] = 1.0 for all dates",
        )
    )

    buy_hold_symbols = ["SPY", "QQQ", "IWM", "EFA", "EEM", "TLT", "IEF", "AGG", "GLD", "DBC", "UUP", "MTUM", "VLUE", "QUAL", "USMV", "QLD", "TQQQ"]
    for symbol in buy_hold_symbols:
        if symbol == benchmark_symbol:
            continue
        if symbol in close:
            results.append(
                run_holding_strategy(
                    close=close[symbol],
                    cash=cash,
                    vbt=vbt,
                    costs=costs,
                    strategy_id=f"buy_hold_{symbol.lower()}",
                    name=f"Buy & Hold {symbol}",
                    family="asset_buy_hold",
                    description=f"Hold {symbol} at 100% allocation for the whole test.",
                    source_code=f"target_weight[{symbol}] = 1.0 for all dates",
                )
            )

    static_blends = [
        ("classic_6040", "Classic 60/40 SPY/AGG", {"SPY": 0.60, "AGG": 0.40}),
        ("all_weather_simple", "All Weather Simple", {"SPY": 0.30, "TLT": 0.40, "IEF": 0.15, "GLD": 0.075, "DBC": 0.075}),
        ("permanent_portfolio", "Permanent Portfolio", {"SPY": 0.25, "TLT": 0.25, "GLD": 0.25, "SHY": 0.25}),
        ("factor_core", "Factor Core MTUM/VLUE/QUAL/USMV", {"SPY": 0.40, "MTUM": 0.20, "VLUE": 0.15, "QUAL": 0.15, "USMV": 0.10}),
        ("value_momentum_quality", "Value Momentum Quality", {"MTUM": 0.34, "VLUE": 0.33, "QUAL": 0.33}),
        ("defensive_factor", "Defensive Factor USMV/QUAL/SPY", {"USMV": 0.40, "QUAL": 0.30, "SPY": 0.30}),
        ("qqq_95_tqqq_05", "QQQ 95% / TQQQ 5%", {"QQQ": 0.95, "TQQQ": 0.05}),
        ("qqq_90_tqqq_10", "QQQ 90% / TQQQ 10%", {"QQQ": 0.90, "TQQQ": 0.10}),
        ("qqq_85_tqqq_15", "QQQ 85% / TQQQ 15%", {"QQQ": 0.85, "TQQQ": 0.15}),
        ("qqq_80_tqqq_20", "QQQ 80% / TQQQ 20%", {"QQQ": 0.8, "TQQQ": 0.2}),
        ("qqq_70_tqqq_30", "QQQ 70% / TQQQ 30%", {"QQQ": 0.7, "TQQQ": 0.3}),
        ("qqq_95_qld_05", "QQQ 95% / QLD 5%", {"QQQ": 0.95, "QLD": 0.05}),
        ("qqq_90_qld_10", "QQQ 90% / QLD 10%", {"QQQ": 0.90, "QLD": 0.10}),
        ("qqq_85_qld_15", "QQQ 85% / QLD 15%", {"QQQ": 0.85, "QLD": 0.15}),
        ("qqq_80_qld_20", "QQQ 80% / QLD 20%", {"QQQ": 0.8, "QLD": 0.2}),
        ("qqq_70_qld_30", "QQQ 70% / QLD 30%", {"QQQ": 0.7, "QLD": 0.3}),
        ("qqq_60_qld_40", "QQQ 60% / QLD 40%", {"QQQ": 0.6, "QLD": 0.4}),
        ("qqq_50_qld_50", "QQQ 50% / QLD 50%", {"QQQ": 0.5, "QLD": 0.5}),
        ("qld_80_shy_20", "QLD 80% / SHY 20%", {"QLD": 0.8, "SHY": 0.2}),
        ("tqqq_50_shy_50", "TQQQ 50% / SHY 50%", {"TQQQ": 0.5, "SHY": 0.5}),
    ]
    for strategy_id, name, allocation in static_blends:
        if all(symbol in close for symbol in allocation):
            assets = list(allocation)
            weights = static_allocation_weights(close.index, allocation)
            results.append(
                run_multi_asset_target_strategy(
                    close=close[assets],
                    weights=weights,
                    cash=cash,
                    vbt=vbt,
                    costs=costs,
                    strategy_id=strategy_id,
                    name=name,
                    family="static_blend",
                    description="Static allocation blend. This is a simple benchmark for controlled leverage.",
                    source_code="\n".join([f"target_weight['{symbol}'] = {weight}" for symbol, weight in allocation.items()]),
                )
            )

    periodic_blends = [
        ("QQQ", "QLD", 0.05),
        ("QQQ", "QLD", 0.10),
        ("QQQ", "QLD", 0.15),
        ("QQQ", "QLD", 0.20),
        ("QQQ", "QLD", 0.25),
        ("QQQ", "QLD", 0.30),
        ("QQQ", "TQQQ", 0.05),
        ("QQQ", "TQQQ", 0.10),
        ("QQQ", "TQQQ", 0.15),
        ("QQQ", "TQQQ", 0.20),
        ("QLD", "SHY", 0.80),
        ("TQQQ", "SHY", 0.50),
    ]
    for base_asset, tilt_asset, tilt_weight in periodic_blends:
        if base_asset not in close or tilt_asset not in close:
            continue
        for rebalance_freq in ["M", "Q"]:
            allocation = {
                base_asset: 1.0 - tilt_weight,
                tilt_asset: tilt_weight,
            }
            if base_asset in ["QLD", "TQQQ"] and tilt_asset == "SHY":
                allocation = {
                    base_asset: tilt_weight,
                    tilt_asset: 1.0 - tilt_weight,
                }
            weights = periodic_static_allocation_weights(close.index, allocation, rebalance_freq)
            freq_name = "Monthly" if rebalance_freq == "M" else "Quarterly"
            tilt_pct = int(tilt_weight * 100)
            results.append(
                run_multi_asset_target_strategy(
                    close=close[list(allocation)],
                    weights=weights,
                    cash=cash,
                    vbt=vbt,
                    costs=costs,
                    strategy_id=f"periodic_{rebalance_freq.lower()}_{base_asset.lower()}_{tilt_asset.lower()}_{tilt_pct}",
                    name=f"{freq_name} {base_asset}/{tilt_asset} Blend {tilt_pct}%",
                    family="periodic_blend",
                    description=f"{freq_name} rebalance static blend between {base_asset} and {tilt_asset}.",
                    source_code="\n".join([f"target_weight['{symbol}'] = {weight}" for symbol, weight in allocation.items()]),
                )
            )

    famous_momentum_assets = ["SPY", "QQQ", "IWM", "EFA", "EEM", "TLT", "IEF", "GLD", "DBC", "UUP"]
    famous_momentum_assets = [asset for asset in famous_momentum_assets if asset in close]
    if "SHY" in close:
        for lookback in [63, 126, 252]:
            for top_n in [1, 2, 3]:
                weights = top_n_absolute_momentum_weights(
                    close=close,
                    assets=famous_momentum_assets,
                    defensive_asset="SHY",
                    lookback=lookback,
                    top_n=top_n,
                    rebalance_freq="M",
                )
                results.append(
                    run_multi_asset_target_strategy(
                        close=close[list(weights.columns)],
                        weights=weights,
                        cash=cash,
                        vbt=vbt,
                        costs=costs,
                        strategy_id=f"top_{top_n}_momentum_{lookback}",
                        name=f"Top-{top_n} ETF Momentum {lookback}D",
                        family="cross_sectional_momentum",
                        description="Monthly cross-sectional momentum. Hold the strongest ETFs only when their own momentum is positive; otherwise hold SHY.",
                        source_code=dedent(
                            f"""
                            momentum = close.pct_change({lookback})
                            every month:
                                selected = top_{top_n}(momentum[{famous_momentum_assets}])
                                hold selected assets with positive momentum equally
                                if none are positive, hold SHY
                            """
                        ).strip(),
                    )
                )

    sector_assets = [asset for asset in SECTOR_ETFS if asset in close]
    if "SHY" in close and sector_assets:
        for lookback in [63, 126, 252]:
            for top_n in [1, 2, 3]:
                weights = top_n_absolute_momentum_weights(
                    close=close,
                    assets=sector_assets,
                    defensive_asset="SHY",
                    lookback=lookback,
                    top_n=top_n,
                    rebalance_freq="M",
                )
                results.append(
                    run_multi_asset_target_strategy(
                        close=close[list(weights.columns)],
                        weights=weights,
                        cash=cash,
                        vbt=vbt,
                        costs=costs,
                        strategy_id=f"sector_top_{top_n}_momentum_{lookback}",
                        name=f"Sector Top-{top_n} Momentum {lookback}D",
                        family="sector_momentum",
                        description="Monthly sector rotation. Hold the strongest sector ETFs with positive momentum; otherwise hold SHY.",
                        source_code=dedent(
                            f"""
                            sector_assets = {sector_assets}
                            momentum = close.pct_change({lookback})
                            every month:
                                selected = top_{top_n}(momentum[sector_assets])
                                hold selected sectors with positive momentum equally
                                if none are positive, hold SHY
                            """
                        ).strip(),
                    )
                )

    stock_assets = [asset for asset in LARGE_CAP_STOCKS if asset in close]
    if "SHY" in close and stock_assets:
        for lookback in [63, 126, 252]:
            for top_n in [3, 5, 10]:
                weights = top_n_absolute_momentum_weights(
                    close=close,
                    assets=stock_assets,
                    defensive_asset="SHY",
                    lookback=lookback,
                    top_n=top_n,
                    rebalance_freq="M",
                )
                results.append(
                    run_multi_asset_target_strategy(
                        close=close[list(weights.columns)],
                        weights=weights,
                        cash=cash,
                        vbt=vbt,
                        costs=costs,
                        strategy_id=f"large_cap_top_{top_n}_momentum_{lookback}",
                        name=f"Large-Cap Top-{top_n} Momentum {lookback}D",
                        family="large_cap_momentum",
                        description="Monthly large-cap stock momentum over the current hand-picked liquid stock universe. This is useful for research but has survivorship bias.",
                        source_code=dedent(
                            f"""
                            stock_universe = {stock_assets}
                            momentum = close.pct_change({lookback})
                            every month:
                                selected = top_{top_n}(momentum[stock_universe])
                                hold selected stocks with positive momentum equally
                                if none are positive, hold SHY
                            """
                        ).strip(),
                    )
                )

        for lookback in [63, 126, 252]:
            for top_n in [5, 10]:
                weights = top_n_absolute_momentum_weights(
                    close=close,
                    assets=stock_assets,
                    defensive_asset="SHY",
                    lookback=lookback,
                    top_n=top_n,
                    rebalance_freq="Q",
                )
                results.append(
                    run_multi_asset_target_strategy(
                        close=close[list(weights.columns)],
                        weights=weights,
                        cash=cash,
                        vbt=vbt,
                        costs=costs,
                        strategy_id=f"quarterly_large_cap_top_{top_n}_momentum_{lookback}",
                        name=f"Quarterly Large-Cap Top-{top_n} Momentum {lookback}D",
                        family="large_cap_momentum",
                        description="Quarterly large-cap stock momentum with lower turnover than the monthly version. Current-list survivorship bias still applies.",
                        source_code=dedent(
                            f"""
                            stock_universe = {stock_assets}
                            momentum = close.pct_change({lookback})
                            every quarter:
                                selected = top_{top_n}(momentum[stock_universe])
                                hold selected stocks with positive momentum equally
                                if none are positive, hold SHY
                            """
                        ).strip(),
                    )
                )

    if all(asset in close for asset in ["SPY", "EFA", "AGG", "SHY"]):
        for lookback in [126, 252]:
            weights = dual_momentum_weights(
                close=close,
                risk_assets=["SPY", "EFA"],
                defensive_assets=["AGG", "SHY"],
                absolute_asset="SPY",
                cash_asset="SHY",
                lookback=lookback,
            )
            results.append(
                run_multi_asset_target_strategy(
                    close=close[list(weights.columns)],
                    weights=weights,
                    cash=cash,
                    vbt=vbt,
                    costs=costs,
                    strategy_id=f"dual_momentum_spy_efa_{lookback}",
                    name=f"Dual Momentum SPY/EFA {lookback}D",
                    family="dual_momentum",
                    description="Gary Antonacci-style ETF dual momentum: choose the stronger of US/international equities only when absolute momentum is positive; otherwise hold bonds/cash.",
                    source_code=dedent(
                        f"""
                        risk_momentum = pct_change({lookback}) for SPY and EFA
                        absolute_filter = SPY.pct_change({lookback}) > SHY.pct_change({lookback})
                        if absolute_filter:
                            hold stronger of SPY and EFA
                        else:
                            hold stronger of AGG and SHY
                        """
                    ).strip(),
                )
            )

    risk_parity_sets = [
        ("risk_parity_all_weather", "Risk Parity All Weather", ["SPY", "TLT", "IEF", "GLD", "DBC"]),
        ("risk_parity_global_macro", "Risk Parity Global Macro", ["SPY", "EFA", "EEM", "TLT", "GLD", "DBC", "UUP"]),
        ("risk_parity_equity_bond_gold", "Risk Parity Equity/Bond/Gold", ["SPY", "TLT", "GLD"]),
    ]
    for strategy_id, name, assets in risk_parity_sets:
        if not all(asset in close for asset in assets):
            continue
        for rebalance_freq in ["M", "Q"]:
            weights = inverse_volatility_weights(
                close=close,
                assets=assets,
                realized_window=63,
                rebalance_freq=rebalance_freq,
                max_asset_weight=0.45,
            )
            freq_name = "Monthly" if rebalance_freq == "M" else "Quarterly"
            results.append(
                run_multi_asset_target_strategy(
                    close=close[assets],
                    weights=weights,
                    cash=cash,
                    vbt=vbt,
                    costs=costs,
                    strategy_id=f"{strategy_id}_{rebalance_freq.lower()}",
                    name=f"{freq_name} {name}",
                    family="risk_parity",
                    description="Risk parity lite: allocate more capital to lower-volatility assets using inverse realized volatility.",
                    source_code=dedent(
                        f"""
                        realized_vol = returns.rolling(63).std() * sqrt(252)
                        raw_weight = 1 / realized_vol
                        cap each asset at 45%
                        rebalance {freq_name.lower()}
                        """
                    ).strip(),
                )
            )

    if all(asset in close for asset in ["SPY", "QQQ"]):
        for lookback in [60, 120]:
            for entry_z in [1.5, 2.0]:
                weights = pairs_mean_reversion_weights(
                    close=close,
                    asset_a="QQQ",
                    asset_b="SPY",
                    lookback=lookback,
                    entry_z=entry_z,
                    exit_z=0.5,
                    gross_exposure=1.0,
                )
                results.append(
                    run_multi_asset_target_strategy(
                        close=close[["QQQ", "SPY"]],
                        weights=weights,
                        cash=cash,
                        vbt=vbt,
                        costs=costs,
                        strategy_id=f"pairs_qqq_spy_{lookback}_{str(entry_z).replace('.', '')}",
                        name=f"Pairs Mean Reversion QQQ/SPY {lookback}D z{entry_z}",
                        family="stat_arb_pairs",
                        description="Simple pairs-trading approximation. Long the relatively cheap ETF and short the relatively rich ETF when the QQQ/SPY spread is stretched.",
                        source_code=dedent(
                            f"""
                            spread = log(QQQ) - log(SPY)
                            z = (spread - rolling_mean({lookback})) / rolling_std({lookback})
                            if z > {entry_z}: short QQQ, long SPY
                            if z < -{entry_z}: long QQQ, short SPY
                            exit when abs(z) < 0.5
                            """
                        ).strip(),
                    )
                )

    for asset in ["QQQ", "QLD", "TQQQ"]:
        if asset not in close or "SHY" not in close:
            continue
        for target_vol in [0.16, 0.20, 0.22, 0.25, 0.28, 0.30, 0.35, 0.40]:
            for rebalance_freq in ["W", "M", "Q"]:
                max_weight = 1.0 if asset == "TQQQ" else 1.5
                weights = volatility_target_weights(
                    close=close,
                    asset=asset,
                    cash_asset="SHY",
                    target_vol=target_vol,
                    realized_window=20,
                    rebalance_freq=rebalance_freq,
                    max_weight=max_weight,
                )
                freq_name = {
                    "W": "Weekly",
                    "M": "Monthly",
                    "Q": "Quarterly",
                }[rebalance_freq]
                results.append(
                    run_multi_asset_target_strategy(
                        close=close[[asset, "SHY"]],
                        weights=weights,
                        cash=cash,
                        vbt=vbt,
                        costs=costs,
                        strategy_id=f"vol_target_{rebalance_freq.lower()}_{asset.lower()}_{int(target_vol * 100)}",
                        name=f"{freq_name} {asset} Vol Target {int(target_vol * 100)}%",
                        family="volatility_target",
                        description=f"Rebalance {freq_name.lower()} between {asset} and SHY to target {target_vol:.0%} annualized volatility.",
                        source_code=dedent(
                            f"""
                            realized_vol = {asset}.returns.rolling(20).std() * sqrt(252)
                            risk_weight = clip({target_vol} / realized_vol, 0, {max_weight})
                            if rebalance_day == '{rebalance_freq}':
                                target_weight['{asset}'] = risk_weight
                                target_weight['SHY'] = 1 - risk_weight
                            """
                        ).strip(),
                    )
                )

    for fast in [20, 50, 75, 100, 125]:
        for slow in [100, 150, 200, 250]:
            if fast >= slow:
                continue
            entries, exits = sma_cross_entries_exits(benchmark_close, fast, slow)
            results.append(
                run_signal_strategy(
                    close=benchmark_close,
                    entries=entries,
                    exits=exits,
                    cash=cash,
                    vbt=vbt,
                    costs=costs,
                    strategy_id=f"{benchmark_symbol.lower()}_sma_cross_{fast}_{slow}",
                    name=f"{benchmark_symbol} SMA Cross {fast}/{slow}",
                    family="sma_cross",
                    description=f"Own {benchmark_symbol} only when the fast SMA is above the slow SMA.",
                    source_code=dedent(
                        f"""
                        fast_ma = {benchmark_symbol}.close.rolling({fast}).mean()
                        slow_ma = {benchmark_symbol}.close.rolling({slow}).mean()
                        if fast_ma > slow_ma:
                            target_weight['{benchmark_symbol}'] = 1.0
                        else:
                            target_weight['{benchmark_symbol}'] = 0.0
                        """
                    ).strip(),
                )
            )

            weights = sma_partial_weights(benchmark_close, fast, slow, uptrend_weight=1.0, downtrend_weight=0.5)
            results.append(
                run_single_asset_target_strategy(
                    close=benchmark_close,
                    weights=weights,
                    cash=cash,
                    vbt=vbt,
                    costs=costs,
                    strategy_id=f"{benchmark_symbol.lower()}_sma_partial_{fast}_{slow}",
                    name=f"{benchmark_symbol} SMA Partial {fast}/{slow}",
                    family="sma_partial",
                    description=f"Hold {benchmark_symbol} 100% in uptrends and 50% in downtrends.",
                    source_code=dedent(
                        f"""
                        fast_ma = {benchmark_symbol}.close.rolling({fast}).mean()
                        slow_ma = {benchmark_symbol}.close.rolling({slow}).mean()
                        if fast_ma > slow_ma:
                            target_weight['{benchmark_symbol}'] = 1.0
                        else:
                            target_weight['{benchmark_symbol}'] = 0.5
                        """
                    ).strip(),
                )
            )

    for risk_asset in ["QLD", "TQQQ"]:
        if risk_asset not in close:
            continue
        for down_asset in ["QQQ", "GLD", "SHY"]:
            if down_asset not in close:
                continue
            for fast, slow in [(20, 100), (50, 150), (50, 200), (100, 200), (125, 250)]:
                for risk_weight in [0.05, 0.10, 0.15, 0.18, 0.20, 0.22, 0.25, 0.30, 0.35, 0.40, 0.50, 0.75, 1.00]:
                    weights = trend_blend_weights(
                        close=close,
                        risk_asset=risk_asset,
                        down_asset=down_asset,
                        signal_asset="QQQ",
                        fast=fast,
                        slow=slow,
                        risk_weight=risk_weight,
                    )
                    risk_pct = int(risk_weight * 100)
                    results.append(
                        run_multi_asset_target_strategy(
                            close=close[[risk_asset, down_asset]],
                            weights=weights,
                            cash=cash,
                            vbt=vbt,
                            costs=costs,
                            strategy_id=f"{risk_asset.lower()}_{down_asset.lower()}_trend_blend_{fast}_{slow}_{risk_pct}",
                            name=f"{risk_asset}/{down_asset} Trend Blend {fast}/{slow} {risk_pct}%",
                            family="trend_blend",
                            description=(
                                f"Use QQQ trend as a filter. In uptrends hold {risk_weight:.0%} {risk_asset} "
                                f"and the rest in {down_asset}; in downtrends hold {down_asset}."
                            ),
                            source_code=dedent(
                                f"""
                                fast_ma = QQQ.close.rolling({fast}).mean()
                                slow_ma = QQQ.close.rolling({slow}).mean()
                                if fast_ma > slow_ma:
                                    target_weight['{risk_asset}'] = {risk_weight}
                                    target_weight['{down_asset}'] = {1.0 - risk_weight}
                                else:
                                    target_weight['{risk_asset}'] = 0.0
                                    target_weight['{down_asset}'] = 1.0
                                """
                            ).strip(),
                        )
                    )

        for fast, slow in [(50, 200), (100, 200), (125, 250)]:
            for defensive in ["SHY", "IEF", "GLD"]:
                weights = binary_risk_asset_weights(
                    close=close,
                    risk_asset=risk_asset,
                    defensive_asset=defensive,
                    signal_asset="QQQ",
                    fast=fast,
                    slow=slow,
                )
                results.append(
                    run_multi_asset_target_strategy(
                        close=close[[risk_asset, defensive]],
                        weights=weights,
                        cash=cash,
                        vbt=vbt,
                        costs=costs,
                        strategy_id=f"{risk_asset.lower()}_risk_{defensive.lower()}_{fast}_{slow}",
                        name=f"{risk_asset} Risk-On / {defensive} Risk-Off {fast}/{slow}",
                        family="leveraged_risk_control",
                        description=f"Use QQQ trend as a filter. Hold {risk_asset} in uptrends and {defensive} in downtrends.",
                        source_code=dedent(
                            f"""
                            fast_ma = QQQ.close.rolling({fast}).mean()
                            slow_ma = QQQ.close.rolling({slow}).mean()
                            if fast_ma > slow_ma:
                                target_weight['{risk_asset}'] = 1.0
                                target_weight['{defensive}'] = 0.0
                            else:
                                target_weight['{risk_asset}'] = 0.0
                                target_weight['{defensive}'] = 1.0
                            """
                        ).strip(),
                    )
                )

    for momentum_window in [63, 126]:
        for trend_window in [100, 200]:
            weights = momentum_rotation_weights(
                close=close,
                risk_assets=["QQQ", "QLD"],
                defensive_assets=["SHY", "IEF", "GLD"],
                signal_asset="QQQ",
                momentum_window=momentum_window,
                trend_window=trend_window,
            )
            assets = ["QQQ", "QLD", "SHY", "IEF", "GLD"]
            results.append(
                run_multi_asset_target_strategy(
                    close=close[assets],
                    weights=weights,
                    cash=cash,
                    vbt=vbt,
                    costs=costs,
                    strategy_id=f"momentum_rotation_{momentum_window}_{trend_window}",
                    name=f"Momentum Rotation {momentum_window}/{trend_window}",
                    family="momentum_rotation",
                    description="Pick the strongest risk asset in uptrends, otherwise pick the strongest defensive asset.",
                    source_code=dedent(
                        f"""
                        trend = QQQ.close > QQQ.close.rolling({trend_window}).mean()
                        momentum = close.pct_change({momentum_window})
                        if trend:
                            selected = argmax(momentum[['QQQ', 'QLD']])
                        else:
                            selected = argmax(momentum[['SHY', 'IEF', 'GLD']])
                        target_weight[selected] = 1.0
                        """
                    ).strip(),
                )
            )

    return results


def run_holding_strategy(close, cash, vbt, costs: CostModel, strategy_id, name, family, description, source_code) -> StrategyResult:
    close = close.dropna()
    portfolio = vbt.Portfolio.from_holding(
        close,
        init_cash=cash,
        fees=costs.fee_rate,
        fixed_fees=costs.fixed_fee,
        slippage=costs.slippage,
        freq="1D",
    )
    return package_result(strategy_id, name, family, description, source_code, portfolio)


def run_signal_strategy(close, entries, exits, cash, vbt, costs: CostModel, strategy_id, name, family, description, source_code) -> StrategyResult:
    close = close.dropna()
    entries = entries.reindex(close.index).fillna(False)
    exits = exits.reindex(close.index).fillna(False)
    portfolio = vbt.Portfolio.from_signals(
        close,
        entries,
        exits,
        init_cash=cash,
        fees=costs.fee_rate,
        fixed_fees=costs.fixed_fee,
        slippage=costs.slippage,
        freq="1D",
    )
    return package_result(strategy_id, name, family, description, source_code, portfolio)


def run_single_asset_target_strategy(close, weights, cash, vbt, costs: CostModel, strategy_id, name, family, description, source_code) -> StrategyResult:
    close = close.dropna()
    weights = weights.reindex(close.index).ffill().fillna(0.0)
    rebalance_weights = weights.where(weights.ne(weights.shift()))
    portfolio = vbt.Portfolio.from_orders(
        close,
        size=rebalance_weights,
        size_type="targetpercent",
        init_cash=cash,
        fees=costs.fee_rate,
        fixed_fees=costs.fixed_fee,
        slippage=costs.slippage,
        freq="1D",
    )
    return package_result(strategy_id, name, family, description, source_code, portfolio)


def run_multi_asset_target_strategy(close, weights, cash, vbt, costs: CostModel, strategy_id, name, family, description, source_code) -> StrategyResult:
    close = close.dropna()
    weights = weights.reindex(close.index).ffill().fillna(0.0)
    rebalance_weights = weights.where(weights.ne(weights.shift()).any(axis=1), other=np.nan)
    portfolio = vbt.Portfolio.from_orders(
        close,
        size=rebalance_weights,
        size_type="targetpercent",
        init_cash=cash,
        fees=costs.fee_rate,
        fixed_fees=costs.fixed_fee,
        slippage=costs.slippage,
        cash_sharing=True,
        group_by=True,
        freq="1D",
    )
    return package_result(strategy_id, name, family, description, source_code, portfolio)


def package_result(strategy_id, name, family, description, source_code, portfolio) -> StrategyResult:
    equity = portfolio.value()
    metrics = portfolio_metrics(portfolio)
    return StrategyResult(
        id=strategy_id,
        name=name,
        family=family,
        description=description,
        source_code=source_code,
        metrics=metrics,
        equity_curve=equity,
    )


def portfolio_metrics(portfolio) -> dict[str, float | int | str | bool]:
    stats = portfolio.stats()
    value = portfolio.value()
    start_value = float(value.iloc[0])
    end_value = float(value.iloc[-1])
    years = max((value.index[-1] - value.index[0]).days / 365.25, 1 / 365.25)
    total_return = (end_value / start_value - 1) * 100
    cagr = ((end_value / start_value) ** (1 / years) - 1) * 100
    max_dd = safe_float(stats, "Max Drawdown [%]")
    sharpe = safe_float(stats, "Sharpe Ratio")
    sortino = safe_float(stats, "Sortino Ratio")
    calmar = cagr / max_dd if max_dd else np.nan
    trades = int(stats.get("Total Trades", 0))
    total_fees_paid = safe_float(stats, "Total Fees Paid")

    return {
        "start": value.index[0].date().isoformat(),
        "end": value.index[-1].date().isoformat(),
        "start_value": start_value,
        "end_value": end_value,
        "total_return_pct": total_return,
        "cagr_pct": cagr,
        "max_drawdown_pct": max_dd,
        "sharpe": sharpe,
        "sortino": sortino,
        "calmar": calmar,
        "trades": trades,
        "total_fees_paid": total_fees_paid,
        "fee_drag_pct": total_fees_paid / start_value * 100,
        "exposure_time_pct": exposure_time_pct(portfolio),
    }


def binary_risk_asset_weights(close, risk_asset, defensive_asset, signal_asset, fast, slow) -> pd.DataFrame:
    signal_close = close[signal_asset]
    fast_ma = signal_close.rolling(fast).mean()
    slow_ma = signal_close.rolling(slow).mean()
    risk_on = fast_ma > slow_ma

    weights = pd.DataFrame(0.0, index=close.index, columns=[risk_asset, defensive_asset])
    weights.loc[risk_on.fillna(False), risk_asset] = 1.0
    weights.loc[~risk_on.fillna(False), defensive_asset] = 1.0
    weights[slow_ma.isna()] = 0.0
    return weights


def trend_blend_weights(close, risk_asset, down_asset, signal_asset, fast, slow, risk_weight) -> pd.DataFrame:
    signal_close = close[signal_asset]
    fast_ma = signal_close.rolling(fast).mean()
    slow_ma = signal_close.rolling(slow).mean()
    risk_on = fast_ma > slow_ma

    weights = pd.DataFrame(0.0, index=close.index, columns=[risk_asset, down_asset])
    weights.loc[risk_on.fillna(False), risk_asset] = risk_weight
    weights.loc[risk_on.fillna(False), down_asset] = 1.0 - risk_weight
    weights.loc[~risk_on.fillna(False), down_asset] = 1.0
    weights[slow_ma.isna()] = 0.0
    return weights


def momentum_rotation_weights(close, risk_assets, defensive_assets, signal_asset, momentum_window, trend_window) -> pd.DataFrame:
    signal_close = close[signal_asset]
    trend = signal_close > signal_close.rolling(trend_window).mean()
    momentum = close.pct_change(momentum_window)
    assets = risk_assets + defensive_assets
    weights = pd.DataFrame(0.0, index=close.index, columns=assets)

    for date in close.index:
        if pd.isna(trend.loc[date]) or momentum.loc[date, assets].isna().any():
            continue
        candidates = risk_assets if bool(trend.loc[date]) else defensive_assets
        selected = momentum.loc[date, candidates].idxmax()
        weights.loc[date, selected] = 1.0

    return weights


def top_n_absolute_momentum_weights(close, assets, defensive_asset, lookback, top_n, rebalance_freq) -> pd.DataFrame:
    columns = sorted(set(assets + [defensive_asset]))
    momentum = close[assets].pct_change(lookback)
    rebalance_dates = first_trading_dates(close.index, rebalance_freq)
    weights = pd.DataFrame(np.nan, index=close.index, columns=columns)

    for date in rebalance_dates:
        scores = momentum.loc[date].dropna().sort_values(ascending=False)
        selected = [asset for asset, value in scores.items() if value > 0][:top_n]
        if selected:
            weight = 1.0 / len(selected)
            for asset in selected:
                weights.loc[date, asset] = weight
            weights.loc[date, [asset for asset in columns if asset not in selected]] = 0.0
        else:
            weights.loc[date, defensive_asset] = 1.0
            weights.loc[date, [asset for asset in columns if asset != defensive_asset]] = 0.0

    weights.iloc[0] = 0.0
    weights.iloc[0, weights.columns.get_loc(defensive_asset)] = 1.0
    return weights


def dual_momentum_weights(close, risk_assets, defensive_assets, absolute_asset, cash_asset, lookback) -> pd.DataFrame:
    columns = sorted(set(risk_assets + defensive_assets + [cash_asset]))
    momentum = close[columns].pct_change(lookback)
    rebalance_dates = first_trading_dates(close.index, "M")
    weights = pd.DataFrame(np.nan, index=close.index, columns=columns)

    for date in rebalance_dates:
        row = momentum.loc[date]
        if row[risk_assets + defensive_assets].isna().any():
            weights.loc[date] = 0.0
            weights.loc[date, cash_asset] = 1.0
            continue

        absolute_ok = row[absolute_asset] > row[cash_asset]
        candidates = risk_assets if absolute_ok else defensive_assets
        selected = row[candidates].idxmax()
        weights.loc[date] = 0.0
        weights.loc[date, selected] = 1.0

    weights.iloc[0] = 0.0
    weights.iloc[0, weights.columns.get_loc(cash_asset)] = 1.0
    return weights


def inverse_volatility_weights(close, assets, realized_window, rebalance_freq, max_asset_weight) -> pd.DataFrame:
    realized_vol = close[assets].pct_change().rolling(realized_window).std() * np.sqrt(252)
    rebalance_dates = first_trading_dates(close.index, rebalance_freq)
    weights = pd.DataFrame(np.nan, index=close.index, columns=assets)

    for date in rebalance_dates:
        vol = realized_vol.loc[date].replace(0, np.nan).dropna()
        if len(vol) != len(assets):
            weights.loc[date] = 1.0 / len(assets)
            continue
        raw = 1.0 / vol
        capped = (raw / raw.sum()).clip(upper=max_asset_weight)
        weights.loc[date] = capped / capped.sum()

    weights.iloc[0] = 1.0 / len(assets)
    return weights


def pairs_mean_reversion_weights(close, asset_a, asset_b, lookback, entry_z, exit_z, gross_exposure) -> pd.DataFrame:
    spread = np.log(close[asset_a]) - np.log(close[asset_b])
    zscore = (spread - spread.rolling(lookback).mean()) / spread.rolling(lookback).std()
    weights = pd.DataFrame(0.0, index=close.index, columns=[asset_a, asset_b])

    state = 0
    half_weight = gross_exposure / 2.0
    for date, z_value in zscore.items():
        if pd.isna(z_value):
            continue
        if state == 0:
            if z_value > entry_z:
                state = -1
            elif z_value < -entry_z:
                state = 1
        elif abs(z_value) < exit_z:
            state = 0

        if state == 1:
            weights.loc[date, asset_a] = half_weight
            weights.loc[date, asset_b] = -half_weight
        elif state == -1:
            weights.loc[date, asset_a] = -half_weight
            weights.loc[date, asset_b] = half_weight

    return weights


def volatility_target_weights(
    close: pd.DataFrame,
    asset: str,
    cash_asset: str,
    target_vol: float,
    realized_window: int,
    rebalance_freq: str,
    max_weight: float,
) -> pd.DataFrame:
    realized_vol = close[asset].pct_change().rolling(realized_window).std() * np.sqrt(252)
    risk_weight = (target_vol / realized_vol).clip(lower=0.0, upper=max_weight).fillna(0.0)
    rebalance_dates = first_trading_dates(close.index, rebalance_freq)

    weights = pd.DataFrame(np.nan, index=close.index, columns=[asset, cash_asset])
    weights.loc[rebalance_dates, asset] = risk_weight.loc[rebalance_dates]
    weights.loc[rebalance_dates, cash_asset] = 1.0 - risk_weight.loc[rebalance_dates]
    weights.iloc[0] = [0.0, 1.0]
    return weights


def static_allocation_weights(index: pd.Index, allocation: dict[str, float]) -> pd.DataFrame:
    weights = pd.DataFrame(np.nan, index=index, columns=list(allocation))
    for symbol, weight in allocation.items():
        weights.iloc[0, weights.columns.get_loc(symbol)] = weight
    return weights


def periodic_static_allocation_weights(index: pd.Index, allocation: dict[str, float], rebalance_freq: str) -> pd.DataFrame:
    weights = pd.DataFrame(np.nan, index=index, columns=list(allocation))
    rebalance_dates = first_trading_dates(index, rebalance_freq)
    for symbol, weight in allocation.items():
        weights.loc[rebalance_dates, symbol] = weight
    weights.iloc[0] = [allocation[symbol] for symbol in weights.columns]
    return weights


def first_trading_dates(index: pd.Index, freq: str) -> pd.Index:
    helper = pd.Series(range(len(index)), index=index)
    plain_index = index.tz_convert(None) if getattr(index, "tz", None) is not None else index

    if freq == "W":
        periods = plain_index.to_period("W")
    elif freq == "M":
        periods = plain_index.to_period("M")
    elif freq == "Q":
        periods = plain_index.to_period("Q")
    else:
        raise ValueError(f"Unsupported rebalance frequency: {freq}")

    return helper.groupby(periods).head(1).index


def apply_relative_metrics(result: StrategyResult, benchmark: StrategyResult) -> None:
    m = result.metrics
    b = benchmark.metrics
    m["excess_return_vs_bh_pct"] = float(m["total_return_pct"]) - float(b["total_return_pct"])
    m["cagr_improvement_vs_bh_pct"] = float(m["cagr_pct"]) - float(b["cagr_pct"])
    m["drawdown_improvement_vs_bh_pct"] = float(b["max_drawdown_pct"]) - float(m["max_drawdown_pct"])
    m["sharpe_improvement_vs_bh"] = float(m["sharpe"]) - float(b["sharpe"])
    m["beats_bh_return"] = bool(float(m["total_return_pct"]) > float(b["total_return_pct"]))
    m["beats_bh_score"] = False
    m["subperiod_win_rate_pct"] = subperiod_win_rate_pct(result.equity_curve, benchmark.equity_curve)
    m["worst_subperiod_excess_pct"] = worst_subperiod_excess_pct(result.equity_curve, benchmark.equity_curve)

    trade_penalty = min(float(m["trades"]) * 0.04, 20.0)
    fee_drag_penalty = float(m.get("fee_drag_pct", 0.0)) * 2.0
    drawdown_penalty = max(float(m["max_drawdown_pct"]) - float(b["max_drawdown_pct"]), 0) * 0.25
    m["score"] = (
        100
        + float(m["cagr_improvement_vs_bh_pct"]) * 2.5
        + float(m["drawdown_improvement_vs_bh_pct"]) * 1.5
        + float(m["sharpe_improvement_vs_bh"]) * 25
        + (float(m["calmar"]) - float(b["calmar"])) * 15
        - trade_penalty
        - fee_drag_penalty
        - drawdown_penalty
    )


def subperiod_win_rate_pct(curve: pd.Series, benchmark_curve: pd.Series) -> float:
    periods = subperiod_excess_returns(curve, benchmark_curve)
    if not periods:
        return float("nan")
    return sum(1 for value in periods if value > 0) / len(periods) * 100


def worst_subperiod_excess_pct(curve: pd.Series, benchmark_curve: pd.Series) -> float:
    periods = subperiod_excess_returns(curve, benchmark_curve)
    if not periods:
        return float("nan")
    return min(periods)


def subperiod_excess_returns(curve: pd.Series, benchmark_curve: pd.Series) -> list[float]:
    aligned = pd.concat({"strategy": curve, "benchmark": benchmark_curve}, axis=1).dropna()
    if aligned.empty:
        return []

    plain_index = aligned.index.tz_convert(None) if getattr(aligned.index, "tz", None) is not None else aligned.index
    masks = [
        (plain_index >= pd.Timestamp("2016-01-01")) & (plain_index <= pd.Timestamp("2019-12-31")),
        (plain_index >= pd.Timestamp("2020-01-01")) & (plain_index <= pd.Timestamp("2022-12-31")),
        (plain_index >= pd.Timestamp("2023-01-01")),
    ]
    excess: list[float] = []
    for mask in masks:
        period = aligned.loc[mask]
        if len(period) < 2:
            continue
        strategy_return = (period["strategy"].iloc[-1] / period["strategy"].iloc[0] - 1) * 100
        benchmark_return = (period["benchmark"].iloc[-1] / period["benchmark"].iloc[0] - 1) * 100
        excess.append(float(strategy_return - benchmark_return))
    return excess


def flatten_result(result: StrategyResult) -> dict[str, object]:
    return {
        "id": result.id,
        "name": result.name,
        "family": result.family,
        **result.metrics,
    }


def leaderboard_payload(rows: pd.DataFrame, results: list[StrategyResult]) -> dict[str, object]:
    result_by_id = {result.id: result for result in results}
    sorted_results = [result_by_id[row["id"]] for _, row in rows.iterrows()]

    return {
        "generated_at": pd.Timestamp.utcnow().isoformat(),
        "rows": [serialize_row(row, result_by_id[row["id"]]) for _, row in rows.iterrows()],
        "curves": {result.id: serialize_curve(result.equity_curve) for result in sorted_results},
    }


def serialize_row(row, result: StrategyResult) -> dict[str, object]:
    data = row.to_dict()
    data["description"] = result.description
    data["source_code"] = result.source_code
    data["metrics"] = result.metrics
    return make_json_safe(data)


def serialize_curve(curve: pd.Series) -> list[list[object]]:
    normalized = curve / float(curve.iloc[0]) * 10000
    return [[idx.date().isoformat(), round(float(value), 2)] for idx, value in normalized.items()]


def make_json_safe(value):
    if isinstance(value, dict):
        return {key: make_json_safe(val) for key, val in value.items()}
    if isinstance(value, list):
        return [make_json_safe(item) for item in value]
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating, float)):
        if np.isnan(value) or np.isinf(value):
            return None
        return float(value)
    if isinstance(value, (np.bool_, bool)):
        return bool(value)
    return value


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
    if isinstance(invested, pd.DataFrame):
        invested = invested.any(axis=1)
    return float(invested.mean() * 100)


def render_html(payload: dict[str, object]) -> str:
    json_payload = json.dumps(payload)
    escaped_payload = html.escape(json_payload, quote=False)
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Trader Agent Strategy Leaderboard</title>
<style>
body {{ margin: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; color: #20242a; background: #f7f8fa; }}
header {{ padding: 18px 24px; background: #111827; color: white; }}
h1 {{ margin: 0; font-size: 22px; }}
main {{ display: grid; grid-template-columns: minmax(620px, 1.4fr) minmax(360px, 0.8fr); gap: 16px; padding: 16px; }}
section {{ background: white; border: 1px solid #d8dde6; border-radius: 8px; overflow: hidden; }}
.section-title {{ padding: 12px 14px; border-bottom: 1px solid #d8dde6; font-weight: 700; }}
.table-wrap {{ overflow: auto; max-height: 560px; }}
table {{ width: 100%; border-collapse: collapse; font-size: 13px; }}
th, td {{ padding: 8px 10px; border-bottom: 1px solid #edf0f3; text-align: right; white-space: nowrap; }}
th {{ position: sticky; top: 0; background: #f1f5f9; z-index: 1; cursor: pointer; }}
td.name, th.name {{ text-align: left; }}
tr.selected-row {{ background: #e8f1ff; }}
tr:hover {{ background: #f8fafc; }}
.pill {{ display: inline-block; padding: 2px 6px; border-radius: 999px; background: #e5e7eb; font-size: 11px; }}
.good {{ color: #057a55; font-weight: 700; }}
.bad {{ color: #b42318; font-weight: 700; }}
.panel {{ padding: 14px; }}
.metrics-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 8px; margin-bottom: 12px; }}
.metric {{ background: #f8fafc; border: 1px solid #e5e7eb; padding: 8px; border-radius: 6px; }}
.metric b {{ display: block; font-size: 11px; color: #667085; margin-bottom: 3px; }}
pre {{ background: #0b1020; color: #dbeafe; padding: 12px; overflow: auto; border-radius: 6px; font-size: 12px; }}
#chart {{ width: 100%; height: 360px; border-top: 1px solid #d8dde6; }}
.hint {{ color: #667085; font-size: 13px; padding: 8px 14px 14px; }}
button {{ border: 1px solid #cbd5e1; background: #fff; padding: 6px 10px; border-radius: 6px; cursor: pointer; }}
</style>
</head>
<body>
<header>
  <h1>Trader Agent Strategy Leaderboard</h1>
  <div>Score balances CAGR, drawdown, Sharpe, Calmar, and trade count against QQQ Buy & Hold.</div>
</header>
<main>
  <section>
    <div class="section-title">Leaderboard</div>
    <div class="hint">Click a row for details. Check multiple rows to compare equity curves.</div>
    <div class="table-wrap">
      <table id="leaderboard"></table>
    </div>
  </section>
  <section>
    <div class="section-title">Selected Strategy</div>
    <div id="detail" class="panel"></div>
  </section>
  <section style="grid-column: 1 / -1;">
    <div class="section-title">Comparison Chart <button id="reset">Reset to top + benchmark</button></div>
    <canvas id="chart"></canvas>
  </section>
</main>
<script id="payload" type="application/json">{escaped_payload}</script>
<script>
const payload = JSON.parse(document.getElementById('payload').textContent);
let rows = payload.rows;
let selectedId = rows[0].id;
let checked = new Set([rows[0].id, 'buy_hold_qqq']);
let sortKey = 'score';
let sortDir = -1;
const columns = [
  ['pick', ''],
  ['rank', '#'],
  ['name', 'Strategy'],
  ['score', 'Score'],
  ['total_return_pct', 'Return %'],
  ['cagr_pct', 'CAGR %'],
  ['max_drawdown_pct', 'Max DD %'],
  ['sharpe', 'Sharpe'],
  ['calmar', 'Calmar'],
  ['trades', 'Trades'],
  ['beats_bh_return', 'Ret > BH'],
  ['beats_bh_score', 'Score > BH']
];
function fmt(value, digits=2) {{
  if (value === null || value === undefined) return '';
  if (typeof value === 'boolean') return value ? 'yes' : 'no';
  if (typeof value === 'number') return value.toFixed(digits);
  return value;
}}
function renderTable() {{
  const table = document.getElementById('leaderboard');
  const sorted = [...rows].sort((a,b) => {{
    const av = a[sortKey], bv = b[sortKey];
    if (typeof av === 'string') return av.localeCompare(bv) * sortDir;
    return ((av ?? -Infinity) - (bv ?? -Infinity)) * sortDir;
  }});
  table.innerHTML = '<thead><tr>' + columns.map(([key,label]) => `<th class="${{key==='name'?'name':''}}" data-key="${{key}}">${{label}}</th>`).join('') + '</tr></thead>' +
    '<tbody>' + sorted.map(row => {{
      const cls = row.id === selectedId ? 'selected-row' : '';
      return `<tr class="${{cls}}" data-id="${{row.id}}">
        <td><input type="checkbox" data-check="${{row.id}}" ${{checked.has(row.id) ? 'checked' : ''}}></td>
        <td>${{row.rank}}</td>
        <td class="name"><span class="pill">${{row.family}}</span> ${{row.name}}</td>
        <td>${{fmt(row.score)}}</td>
        <td class="${{row.excess_return_vs_bh_pct > 0 ? 'good' : 'bad'}}">${{fmt(row.total_return_pct)}}</td>
        <td>${{fmt(row.cagr_pct)}}</td>
        <td>${{fmt(row.max_drawdown_pct)}}</td>
        <td>${{fmt(row.sharpe, 3)}}</td>
        <td>${{fmt(row.calmar, 3)}}</td>
        <td>${{row.trades}}</td>
        <td>${{row.beats_bh_return ? '<span class="good">yes</span>' : '<span class="bad">no</span>'}}</td>
        <td>${{row.beats_bh_score ? '<span class="good">yes</span>' : '<span class="bad">no</span>'}}</td>
      </tr>`;
    }}).join('') + '</tbody>';
  table.querySelectorAll('th').forEach(th => th.onclick = () => {{
    const key = th.dataset.key;
    if (!key || key === 'pick') return;
    if (sortKey === key) sortDir *= -1; else {{ sortKey = key; sortDir = -1; }}
    renderTable();
  }});
  table.querySelectorAll('tr[data-id]').forEach(tr => tr.onclick = (event) => {{
    if (event.target.type === 'checkbox') return;
    selectedId = tr.dataset.id;
    renderTable(); renderDetail(); drawChart();
  }});
  table.querySelectorAll('input[data-check]').forEach(input => input.onchange = () => {{
    if (input.checked) checked.add(input.dataset.check); else checked.delete(input.dataset.check);
    drawChart();
  }});
}}
function renderDetail() {{
  const row = rows.find(r => r.id === selectedId);
  const metrics = ['score','total_return_pct','cagr_pct','max_drawdown_pct','sharpe','sortino','calmar','trades','total_fees_paid','fee_drag_pct','exposure_time_pct','excess_return_vs_bh_pct','drawdown_improvement_vs_bh_pct','subperiod_win_rate_pct','worst_subperiod_excess_pct'];
  document.getElementById('detail').innerHTML = `
    <h2>${{row.name}}</h2>
    <p>${{row.description}}</p>
    <div class="metrics-grid">${{metrics.map(k => `<div class="metric"><b>${{k}}</b>${{fmt(row[k], 3)}}</div>`).join('')}}</div>
    <h3>Source / Logic</h3>
    <pre>${{escapeHtml(row.source_code)}}</pre>
  `;
}}
function escapeHtml(text) {{
  return String(text).replace(/[&<>"']/g, ch => ({{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}}[ch]));
}}
function drawChart() {{
  const canvas = document.getElementById('chart');
  const rect = canvas.getBoundingClientRect();
  canvas.width = Math.floor(rect.width * window.devicePixelRatio);
  canvas.height = Math.floor(rect.height * window.devicePixelRatio);
  const ctx = canvas.getContext('2d');
  ctx.scale(window.devicePixelRatio, window.devicePixelRatio);
  const w = rect.width, h = rect.height, pad = 42;
  ctx.clearRect(0,0,w,h);
  const ids = [...checked].filter(id => payload.curves[id]);
  const all = ids.flatMap(id => payload.curves[id].map(p => p[1]));
  const minY = Math.min(...all), maxY = Math.max(...all);
  const colors = ['#111827','#2563eb','#dc2626','#059669','#7c3aed','#ea580c','#0891b2'];
  ctx.strokeStyle = '#e5e7eb'; ctx.lineWidth = 1;
  for (let i=0;i<5;i++) {{
    const y = pad + i*(h-pad*2)/4;
    ctx.beginPath(); ctx.moveTo(pad,y); ctx.lineTo(w-pad,y); ctx.stroke();
  }}
  ids.forEach((id, idx) => {{
    const curve = payload.curves[id];
    ctx.strokeStyle = colors[idx % colors.length]; ctx.lineWidth = 2;
    ctx.beginPath();
    curve.forEach((p, i) => {{
      const x = pad + i*(w-pad*2)/(curve.length-1);
      const y = h-pad - ((p[1]-minY)/(maxY-minY || 1))*(h-pad*2);
      if (i === 0) ctx.moveTo(x,y); else ctx.lineTo(x,y);
    }});
    ctx.stroke();
    const row = rows.find(r => r.id === id);
    ctx.fillStyle = colors[idx % colors.length];
    ctx.fillText(row.name, pad + 8, pad + 16 + idx*16);
  }});
  ctx.fillStyle = '#667085';
  ctx.fillText('$' + Math.round(maxY).toLocaleString(), w-pad+4, pad+4);
  ctx.fillText('$' + Math.round(minY).toLocaleString(), w-pad+4, h-pad);
}}
document.getElementById('reset').onclick = () => {{ checked = new Set([rows[0].id, 'buy_hold_qqq']); drawChart(); renderTable(); }};
window.onresize = drawChart;
renderTable(); renderDetail(); drawChart();
</script>
</body>
</html>"""


if __name__ == "__main__":
    main()
