from lifeforce.trading.strategies.grid_strategy import GridStrategy
from lifeforce.trading.strategies.trend_strategy import TrendStrategy


def test_grid_strategy_backtest() -> None:
    strategy = GridStrategy(symbol="BTC/USDT", grid_size=5, lower_price=90, upper_price=110)
    prices = [100, 95, 92, 96, 104, 108]
    signals = strategy.backtest_signals(prices)
    assert len(signals) == len(prices) - 1
    assert any(signal in {"buy", "sell"} for signal in signals)


def test_trend_strategy_signal() -> None:
    strategy = TrendStrategy(fast_window=3, slow_window=5)
    prices = [10, 10, 10, 10, 10, 11, 12, 13]
    signal = strategy.signal(prices)
    assert signal in {"buy", "sell", "hold"}
