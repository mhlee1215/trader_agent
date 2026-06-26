from AlgorithmImports import *


class RiskOnOffMomentumRotation(QCAlgorithm):
    def initialize(self):
        self.initial_cash = 10000
        self.start_year = 2010
        self.end_year = 2024

        self.risk_on_assets = ["QQQ", "SPY"]
        self.defensive_assets = ["TLT", "GLD", "IEF"]
        self.canary_ticker = "QQQ"
        self.momentum_period = 126
        self.trend_period = 200

        self.set_start_date(self.start_year, 1, 1)
        self.set_end_date(self.end_year, 12, 31)
        self.set_cash(self.initial_cash)

        tickers = sorted(set(self.risk_on_assets + self.defensive_assets + [self.canary_ticker]))
        self.symbols_by_ticker = {
            ticker: self.add_equity(ticker, Resolution.DAILY).symbol
            for ticker in tickers
        }

        self.canary = self.symbols_by_ticker[self.canary_ticker]
        self.canary_sma = self.sma(self.canary, self.trend_period, Resolution.DAILY)

        self.momentum = {
            ticker: self.roc(symbol, self.momentum_period, Resolution.DAILY)
            for ticker, symbol in self.symbols_by_ticker.items()
        }

        self.set_warm_up(max(self.momentum_period, self.trend_period), Resolution.DAILY)
        self.set_benchmark(self.canary_ticker)
        self.set_name("Risk-On Off Momentum Rotation vs QQQ Buy Hold")

        self.current_ticker = None
        self.first_benchmark_price = None

        self.schedule.on(
            self.date_rules.month_start(self.canary_ticker),
            self.time_rules.after_market_open(self.canary_ticker, 30),
            self.rebalance,
        )

    def on_data(self, data):
        if not data.bars.contains_key(self.canary):
            return

        benchmark_price = data.bars[self.canary].close
        self.plot_comparison(benchmark_price)

    def rebalance(self):
        if self.is_warming_up:
            return

        if not self.canary_sma.is_ready:
            return

        if not all(indicator.is_ready for indicator in self.momentum.values()):
            return

        canary_price = self.securities[self.canary].price
        risk_on = canary_price > self.canary_sma.current.value

        candidates = self.risk_on_assets if risk_on else self.defensive_assets
        selected_ticker = max(candidates, key=lambda ticker: self.momentum[ticker].current.value)

        if selected_ticker == self.current_ticker:
            return

        selected_symbol = self.symbols_by_ticker[selected_ticker]

        for ticker, symbol in self.symbols_by_ticker.items():
            if ticker != selected_ticker and self.portfolio[symbol].invested:
                self.liquidate(symbol)

        self.set_holdings(selected_symbol, 1.0)
        self.current_ticker = selected_ticker

        mode = "RISK_ON" if risk_on else "RISK_OFF"
        self.debug(
            f"{self.time.date()} {mode}: selected={selected_ticker}, "
            f"momentum={self.momentum[selected_ticker].current.value:.2%}"
        )

    def plot_comparison(self, benchmark_price):
        if self.first_benchmark_price is None:
            self.first_benchmark_price = benchmark_price

        buy_hold_value = self.initial_cash * (benchmark_price / self.first_benchmark_price)

        self.plot("Comparison", f"Buy & Hold {self.canary_ticker}", buy_hold_value)
        self.plot("Comparison", "Rotation Strategy", self.portfolio.total_portfolio_value)
