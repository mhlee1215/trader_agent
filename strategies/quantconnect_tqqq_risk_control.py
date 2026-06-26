from AlgorithmImports import *


class TqqqRiskControlledTrend(QCAlgorithm):
    def initialize(self):
        self.initial_cash = 10000
        self.set_start_date(2010, 1, 1)
        self.set_end_date(2024, 12, 31)
        self.set_cash(self.initial_cash)

        self.benchmark_ticker = "QQQ"
        self.risk_asset_ticker = "TQQQ"
        self.defensive_tickers = ["IEF", "GLD", "SHY"]

        self.trend_period = 200
        self.momentum_period = 63

        self.benchmark_symbol = self.add_equity(self.benchmark_ticker, Resolution.DAILY).symbol
        self.risk_asset = self.add_equity(self.risk_asset_ticker, Resolution.DAILY).symbol
        self.defensive_assets = {
            ticker: self.add_equity(ticker, Resolution.DAILY).symbol
            for ticker in self.defensive_tickers
        }

        self.qqq_sma = self.sma(self.benchmark_symbol, self.trend_period, Resolution.DAILY)
        self.qqq_momentum = self.roc(self.benchmark_symbol, self.momentum_period, Resolution.DAILY)
        self.defensive_momentum = {
            ticker: self.roc(symbol, self.momentum_period, Resolution.DAILY)
            for ticker, symbol in self.defensive_assets.items()
        }

        self.set_warm_up(self.trend_period, Resolution.DAILY)
        self.set_benchmark(self.benchmark_ticker)
        self.set_name("TQQQ Risk-Controlled Trend vs QQQ Buy Hold")

        self.current_ticker = None
        self.first_benchmark_price = None

        self.schedule.on(
            self.date_rules.week_start(self.benchmark_ticker),
            self.time_rules.after_market_open(self.benchmark_ticker, 30),
            self.rebalance,
        )

    def on_data(self, data):
        if not data.bars.contains_key(self.benchmark_symbol):
            return

        self.plot_comparison(data.bars[self.benchmark_symbol].close)

    def rebalance(self):
        if self.is_warming_up:
            return

        if not self.qqq_sma.is_ready or not self.qqq_momentum.is_ready:
            return

        if not all(indicator.is_ready for indicator in self.defensive_momentum.values()):
            return

        qqq_price = self.securities[self.benchmark_symbol].price
        trend_ok = qqq_price > self.qqq_sma.current.value
        momentum_ok = self.qqq_momentum.current.value > 0

        if trend_ok and momentum_ok:
            selected_ticker = self.risk_asset_ticker
            selected_symbol = self.risk_asset
            mode = "RISK_ON"
        else:
            selected_ticker = max(
                self.defensive_tickers,
                key=lambda ticker: self.defensive_momentum[ticker].current.value,
            )
            selected_symbol = self.defensive_assets[selected_ticker]
            mode = "RISK_OFF"

        if selected_ticker == self.current_ticker:
            return

        self.liquidate()
        self.set_holdings(selected_symbol, 1.0)
        self.current_ticker = selected_ticker

        self.debug(
            f"{self.time.date()} {mode}: selected={selected_ticker}, "
            f"QQQ price={qqq_price:.2f}, "
            f"SMA={self.qqq_sma.current.value:.2f}, "
            f"QQQ momentum={self.qqq_momentum.current.value:.2%}"
        )

    def plot_comparison(self, benchmark_price):
        if self.first_benchmark_price is None:
            self.first_benchmark_price = benchmark_price

        buy_hold_value = self.initial_cash * (benchmark_price / self.first_benchmark_price)

        self.plot("Comparison", f"Buy & Hold {self.benchmark_ticker}", buy_hold_value)
        self.plot("Comparison", "Risk-Controlled TQQQ", self.portfolio.total_portfolio_value)
