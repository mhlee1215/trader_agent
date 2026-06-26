# Trading Harness Shortlist

Goal: find an existing harness or scaffold for:

```text
strategy research
→ backtesting
→ result reporting
→ Alpaca paper trading
→ later live deployment gates
```

## Best Fit For This Project

Build a small local harness around `vectorbt` and `alpaca-py`.

Reason:

- Existing full trading harnesses are either too broad, too agentic, too crypto-focused, or not clearly mature enough for beginner-safe use.
- `vectorbt` is the strongest research engine for local parameter sweeps.
- `alpaca-py` is the official Alpaca SDK for market data and paper/live trading.
- A small harness lets us keep safety rules, logs, and paper/live gates explicit.

## External Candidates

| Candidate | What It Is | Verdict | Notes |
| --- | --- | --- | --- |
| TradeSight | Self-hosted Alpaca strategy lab with dashboard and paper trading | Watch / maybe inspect | Close to the desired idea, but likely heavier than needed. |
| AlpacaCode | CLI for Alpaca backtesting, paper trading, reporting, agent pipeline | Watch / inspect carefully | Interesting, but new and may require extra services like database/API keys. |
| Lumibot | Backtest, paper, live framework with Alpaca support | Maybe later | Good if we want one framework for paper/live, but more abstraction than needed now. |
| alpaca-backtrader-api | Alpaca integration for Backtrader | Maybe later | Useful if switching to Backtrader; less ideal than newer `alpaca-py` path. |
| OpenTradex | Broad local trading cockpit with Alpaca connector | Too broad for now | More cockpit/agent platform than research harness. |
| OpenProphet | Agentic Alpaca trading MCP/harness | Not for beginner trading bot | Interesting but too autonomous and risky for this stage. |
| FinRL-Trading | AI/ML quant infrastructure with paper trading | Later only | Better for ML/RL experiments after baseline rules are solid. |

## Recommended Local Harness Shape

```text
data/
  cached Alpaca bars

src/
  data/
    fetch_alpaca.py
  research/
    run_vectorbt_sweep.py
    strategies.py
    metrics.py
  paper/
    generate_signal.py
    place_order_alpaca.py
    reconcile_positions.py
  safety/
    checks.py
    kill_switch.py
  reports/
    write_markdown_report.py
```

## Minimum Harness Commands

```bash
python -m src.data.fetch_alpaca --symbols QQQ SPY IEF GLD SHY
python -m src.research.run_vectorbt_sweep --config configs/qqq_sma.yml
python -m src.paper.generate_signal --strategy qqq_sma_50_200 --dry-run
python -m src.paper.place_order_alpaca --paper --dry-run
```

## Safety Gates

- Paper mode is default.
- Live mode requires explicit `TRADING_MODE=live`.
- Kill switch must be checked before every order.
- No order is submitted unless target allocation differs from current position.
- Every decision writes a log entry.
- Backtest result must be saved before strategy can be enabled for paper trading.
