# QuantConnect Beginner Steps

## Goal

Run one strategy and compare it against simply buying and holding SPY.

## Workflow

1. Open QuantConnect Algorithm Lab.
2. Create a Python project.
3. Replace `main.py` with the code from `strategies/quantconnect_spy_ma_vs_buy_hold.py`.
4. Click Backtest.
5. Compare the `Comparison` chart:
   - `Buy & Hold SPY`
   - `MA Strategy`
6. Record these numbers in `docs/experiment_log.md`:
   - Return
   - Drawdown
   - Sharpe ratio
   - Total trades

## Rule

Do not deploy live trading yet. Use QuantConnect only for backtesting until the strategy has been compared against a simple benchmark.
