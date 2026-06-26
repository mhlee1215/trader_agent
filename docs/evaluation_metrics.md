# Strategy Evaluation Metrics

Use these metrics for every strategy. Do not judge a strategy by total return alone.

## Primary Scorecard

| Metric | Why It Matters | Preferred Direction |
| --- | --- | --- |
| Total Return [%] | Shows total growth over the full test period | Higher |
| CAGR [%] | Annualized return, easier to compare across periods | Higher |
| Max Drawdown [%] | Worst peak-to-trough loss; key survivability metric | Lower |
| Sharpe Ratio | Return per unit of volatility | Higher |
| Sortino Ratio | Return per unit of downside volatility | Higher |
| Calmar Ratio | CAGR divided by max drawdown | Higher |
| Total Trades | Shows complexity and turnover | Lower, unless justified |
| Total Fees Paid | Estimated execution costs from fees, fixed ticket cost, and slippage inputs | Lower |
| Fee Drag [%] | Total fees divided by starting cash; important for small accounts | Lower |
| Exposure [%] | How much time capital is actually invested | Context dependent |
| Final Value | Ending account value from fixed starting cash | Higher |

## One-Number Score

The leaderboard uses one composite score so strategies can be ranked quickly.

```text
score =
  100
  + CAGR improvement vs buy hold * 2.5
  + Drawdown improvement vs buy hold * 1.5
  + Sharpe improvement vs buy hold * 25
  + Calmar improvement vs buy hold * 15
  - Trade penalty
  - Fee drag penalty
  - Extra drawdown penalty
```

Interpretation:

- `100` is roughly the buy-and-hold reference point.
- Above `100` means the strategy is better than buy and hold by this risk-adjusted score.
- `beats_bh_return` is separate and means raw total return is higher than buy and hold.
- A leveraged strategy can beat return while losing on score if drawdown is too large.
- A defensive strategy can beat score while losing on raw return if drawdown and risk-adjusted metrics improve enough.
- A high-turnover strategy can lose on score even when raw return looks strong, because small-account fees and slippage matter.

Current default cost model:

```text
Starting Cash = $3,000
Percent Fee = 0.01% per order
Fixed Fee = $0.25 per order
Slippage = 0.05%
```

## Benchmark Metrics

Every report must include buy and hold for the same asset and date range.

| Metric | Why It Matters |
| --- | --- |
| Excess Return vs Buy Hold [%] | Strategy return minus benchmark return |
| Drawdown Improvement [%] | Benchmark drawdown minus strategy drawdown |
| Sharpe Improvement | Strategy Sharpe minus benchmark Sharpe |

## Minimum Acceptance Rules

A strategy is not interesting unless at least one of these is true:

- It beats buy and hold total return without much worse drawdown.
- It has similar return with meaningfully lower drawdown.
- It has lower return but much better Sharpe, Sortino, or Calmar.
- It has simple rules, low trade count, and works across multiple periods.

## Rejection Rules

Reject or pause strategies with:

- High return but extreme drawdown.
- Good result in only one cherry-picked period.
- More complexity without better drawdown or Sharpe.
- Excessive trades or fees.
- Any logic that cannot be reused in paper trading.

## Current Default Benchmark

For QQQ strategies:

```text
Benchmark = QQQ Buy & Hold
Start Cash = $3,000
Default Cached Date Range = 2016-01-04 to latest cached data
```
