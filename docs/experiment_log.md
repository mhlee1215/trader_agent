# Trading Bot Experiment Log

Use the same dates and starting cash when comparing strategies.

## Baseline

| Strategy | Ticker | Period | Exposure | Return | Drawdown | Sharpe | Trades | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Buy & Hold | SPY | 2019-01-01 to 2024-12-31 | 100% | 156.19% | TBD | TBD | 1 | First benchmark result from QuantConnect |
| SMA 20/50 | SPY | 2019-01-01 to 2024-12-31 | 20% | 10.11% | TBD | TBD | TBD | Initial beginner strategy |
| SMA 20/50 | SPY | 2019-01-01 to 2024-12-31 | 100% | 61.34% | TBD | TBD | TBD | More fair comparison against buy and hold |
| SMA 50/200 | SPY | 2019-01-01 to 2024-12-31 | 100% | 83.19% | 33.10% | 0.418 | 5 | Fewer trades and better return than SMA 20/50, but still trails buy and hold |
| SMA 50/200 | QQQ | 2019-01-01 to 2024-12-31 | 100% | 223.03% | TBD | TBD | TBD | Strong return result; record risk metrics next |
| SMA 50/200 partial | QQQ | 2010-01-01 to 2024-12-31 | 100% uptrend / 50% downtrend | 935.72% | 28.50% | 0.719 | 17 | Better than the daily-rebalanced version, but still trails QQQ buy and hold over the long period |
| Risk-on/off rotation | QQQ/SPY/TLT/GLD/IEF | 2010-01-01 to 2024-12-31 | 100% selected asset | 430.10% | 33.70% | 0.507 | 95 | Discard candidate: lower return, worse drawdown, and more turnover than simpler QQQ timing tests |
| TQQQ risk-controlled trend | QQQ/TQQQ/IEF/GLD/SHY | 2010-01-01 to 2024-12-31 | 100% selected asset | 1320.09% | 62.00% | 0.525 | 201 | Discard candidate for beginner use: high return but extreme drawdown, high fees, and high turnover |
| vectorbt baseline buy hold | QQQ | 2016-01-04 to 2026-06-08 | 100% | 553.88% | 35.62% | 1.112 | 1 | Alpaca local baseline; actual cached data starts in 2016 |
| vectorbt SMA partial 100/200 | QQQ | 2016-01-04 to 2026-06-08 | 100% uptrend / 50% downtrend | 494.88% | 28.56% | 1.158 | 4 | Current best score candidate: lower return than buy hold, better drawdown and Sharpe |
| Weekly QQQ Vol Target 25% | QQQ/SHY | 2016-01-04 to 2026-06-08 | Weekly volatility target | 844.81% | 32.44% | 1.266 | 421 | Current top leaderboard candidate; beats QQQ buy hold by return and score, but has high trade count |
| QQQ buy hold, small account | QQQ | 2016-01-04 to 2026-06-08 | 100% | 606.25% | 35.00% | 1.152 | 1 | `$3,000` starting cash with fee/slippage model; benchmark score `99.92` |
| TQQQ/GLD trend blend 20/100 25% | TQQQ/GLD | 2016-01-04 to 2026-06-08 | 25% TQQQ in QQQ uptrends, otherwise GLD | 309.46% | 20.04% | 1.183 | 11 | Top score under `$3,000` fee model; much lower drawdown but does not beat QQQ raw return |
| TQQQ/QQQ trend blend 20/100 10% | TQQQ/QQQ | 2016-01-04 to 2026-06-08 | 10% TQQQ tilt in QQQ uptrends, otherwise QQQ | 606.62% | 33.43% | 1.181 | 11 | Beats QQQ by both raw return and score, but only barely; needs regime split and out-of-sample validation |
| TQQQ/QQQ trend blend 20/100 5% | TQQQ/QQQ | 2016-01-04 to 2026-06-08 | 5% TQQQ tilt in QQQ uptrends, otherwise QQQ | 606.66% | 34.23% | 1.174 | 11 | Also barely beats QQQ by return and score; likely fragile edge |
| QQQ 95% / QLD 5% | QQQ/QLD | 2016-01-04 to 2026-06-08 | Static 5% QLD tilt | 669.67% | 38.31% | 1.128 | 2 | Simple raw-return improvement; worse drawdown and lower score than QQQ buy hold |

## Next Experiments

- [ ] Record drawdown, Sharpe ratio, and total trades for Buy & Hold.
- [ ] Record drawdown, Sharpe ratio, and total trades for SMA 20/50.
- [ ] Test SMA 50/200 with 100% exposure.
- [ ] Test the same strategy on QQQ.
- [ ] Test a risk-off version that moves to cash during downtrends.
- [ ] Test monthly risk-on/risk-off momentum rotation with QQQ/SPY and TLT/GLD/IEF.
- [ ] Test aggressive TQQQ risk-controlled trend strategy against QQQ buy and hold.
- [x] Add small-account fee and slippage model with `$3,000` starting cash.
- [x] Add low-turnover trend-blend candidates.
- [x] Add simple low-turnover QQQ/QLD and QQQ/TQQQ tilt candidates.
- [ ] Compare static QQQ 95% / QLD 5% against trend-blend candidates by regime.
- [ ] Split TQQQ/QQQ 5-10% trend blend by market regime.
- [ ] Check whether the tiny TQQQ tilt edge survives different start dates.
