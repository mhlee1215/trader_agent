from __future__ import annotations

import pandas as pd


def sma_cross_entries_exits(close: pd.Series, fast: int, slow: int) -> tuple[pd.Series, pd.Series]:
    if fast >= slow:
        raise ValueError("fast must be less than slow")

    fast_ma = close.rolling(fast).mean()
    slow_ma = close.rolling(slow).mean()
    signal = fast_ma > slow_ma

    previous_signal = signal.shift(1, fill_value=False).astype(bool)
    entries = signal & ~previous_signal
    exits = ~signal & previous_signal
    return entries, exits


def sma_partial_weights(
    close: pd.Series,
    fast: int,
    slow: int,
    uptrend_weight: float = 1.0,
    downtrend_weight: float = 0.5,
) -> pd.Series:
    if fast >= slow:
        raise ValueError("fast must be less than slow")

    fast_ma = close.rolling(fast).mean()
    slow_ma = close.rolling(slow).mean()
    weights = pd.Series(downtrend_weight, index=close.index, dtype=float)
    weights[fast_ma > slow_ma] = uptrend_weight
    weights[slow_ma.isna()] = 0.0
    return weights


def latest_sma_target(
    close: pd.Series,
    fast: int,
    slow: int,
    uptrend_weight: float = 1.0,
    downtrend_weight: float = 0.5,
) -> dict[str, float | str]:
    if len(close) < slow:
        raise ValueError(f"Need at least {slow} close prices")

    fast_value = float(close.tail(fast).mean())
    slow_value = float(close.tail(slow).mean())
    target = uptrend_weight if fast_value > slow_value else downtrend_weight
    regime = "uptrend" if fast_value > slow_value else "downtrend"

    return {
        "fast_sma": fast_value,
        "slow_sma": slow_value,
        "target_weight": target,
        "regime": regime,
    }
