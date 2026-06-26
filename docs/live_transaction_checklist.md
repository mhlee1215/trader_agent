# Alpaca Live Transaction Checklist

This thread is for live account transaction handling only. Strategy research stays in the main algorithm thread.

## Current State

- `src.trading.account_status` can read paper or live account status without submitting orders.
- `src.paper.rebalance_large_cap_momentum` supports `--account paper` and `--account live`.
- Paper and live use separate credential env names and separate kill switches.
- Live execution is blocked unless `LIVE_TRADING_KILL_SWITCH=false`, limits pass, market is open, and `--confirm-live-submit I_APPROVE_LIVE_ORDER` is present.
- See `docs/paper_live_pipeline.md`.

## Live Test Must Not Start Until

- [ ] Live API credentials are stored locally without being printed in chat or committed.
- [x] Live mode uses separate env names from paper mode.
- [x] A live-specific kill switch exists: `LIVE_TRADING_KILL_SWITCH=true`.
- [x] Maximum live order notional is enforced in code.
- [x] Maximum total live deployment amount is enforced in code.
- [x] Duplicate open-order checks run before every order.
- [x] Current live positions are read before every order.
- [x] Cash/buying power is read before every order.
- [x] Market-hours status is checked before live order submission.
- [x] The user receives a dry-run preview before every live order.
- [x] The user explicitly approves every live order immediately before submission.
- [ ] The order result is verified after submission.
- [ ] The thread reports order id, status, filled quantity, average fill price, cash, positions, and any error.

## Recommended First Live Test

Use a tiny manual transaction, not an algorithmic rebalance.

Example policy:

```text
Max first order: $5-$25
Order type: limit order preferred
Symbol: highly liquid ETF or stock
Automation: none
```

## Prohibited For Now

- No automatic live rebalancing.
- No scheduled live orders.
- No live use by manually changing `paper=True` to `paper=False`; use `--account live` only.
- No live orders from strategy research outputs without a separate transaction preview.
- No live order if account type or endpoint cannot be confirmed.

## Live Transaction Flow

1. User asks for a specific live test order.
2. Thread verifies live credentials and live account access without printing secrets.
3. Thread checks current cash, positions, and open orders.
4. Thread creates a dry-run order preview.
5. User explicitly confirms the exact order.
6. Thread temporarily opens the live kill switch only if needed.
7. Thread submits the order.
8. Thread immediately restores the kill switch.
9. Thread verifies order status and reports the result.
