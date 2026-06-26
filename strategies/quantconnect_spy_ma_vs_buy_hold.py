from AlgorithmImports import *


class MovingAverageVsBuyHold(QCAlgorithm):
    def initialize(self):
        # Change these values for each experiment.
        self.ticker = "QQQ"
        self.fast_period = 50
        self.slow_period = 200
        self.target_weight = 1.0
        self.initial_cash = 10000

        self.set_start_date(2019, 1, 1)
        self.set_end_date(2024, 12, 31)
        self.set_cash(self.initial_cash)

        self.symbol = self.add_equity(self.ticker, Resolution.DAILY).symbol
        self.fast = self.sma(self.symbol, self.fast_period, Resolution.DAILY)
        self.slow = self.sma(self.symbol, self.slow_period, Resolution.DAILY)

        self.set_warm_up(self.slow_period, Resolution.DAILY)
        self.set_benchmark(self.ticker)
        self.set_name(f"{self.ticker} SMA {self.fast_period}/{self.slow_period} vs Buy Hold")

        self.first_price = None

    def on_data(self, data):
        if not data.bars.contains_key(self.symbol):
            return

        bar = data.bars[self.symbol]
        if bar is None:
            return

        self.plot_comparison(bar.close)

        if self.is_warming_up:
            return

        if not self.fast.is_ready or not self.slow.is_ready:
            return

        invested = self.portfolio[self.symbol].invested
        fast_above_slow = self.fast.current.value > self.slow.current.value

        if fast_above_slow and not invested:
            self.set_holdings(self.symbol, self.target_weight)
            self.debug(
                f"BUY {self.ticker}: "
                f"fast={self.fast.current.value:.2f}, "
                f"slow={self.slow.current.value:.2f}"
            )

        elif not fast_above_slow and invested:
            self.liquidate(self.symbol)
            self.debug(
                f"SELL {self.ticker}: "
                f"fast={self.fast.current.value:.2f}, "
                f"slow={self.slow.current.value:.2f}"
            )

    def plot_comparison(self, price):
        if self.first_price is None:
            self.first_price = price

        buy_hold_value = self.initial_cash * (price / self.first_price)

        self.plot("Comparison", f"Buy & Hold {self.ticker}", buy_hold_value)
        self.plot("Comparison", "MA Strategy", self.portfolio.total_portfolio_value)
