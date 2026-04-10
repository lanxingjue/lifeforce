"""网格交易策略。"""

from dataclasses import dataclass
from typing import List


@dataclass
class GridStrategy:
    symbol: str
    grid_size: int = 10
    lower_price: float = 60000.0
    upper_price: float = 70000.0
    investment: float = 1000.0

    def __post_init__(self) -> None:
        if self.grid_size < 2:
            self.grid_size = 2
        step = (self.upper_price - self.lower_price) / (self.grid_size - 1)
        self.grid_levels = [self.lower_price + i * step for i in range(self.grid_size)]

    def should_buy(self, current_price: float, last_price: float) -> bool:
        crossed = any(last_price > level >= current_price for level in self.grid_levels)
        return crossed and current_price <= self.upper_price

    def should_sell(self, current_price: float, last_price: float) -> bool:
        crossed = any(last_price < level <= current_price for level in self.grid_levels)
        return crossed and current_price >= self.lower_price

    def generate_signal(self, current_price: float, last_price: float) -> str:
        if self.should_buy(current_price, last_price):
            return "buy"
        if self.should_sell(current_price, last_price):
            return "sell"
        return "hold"

    def backtest_signals(self, prices: List[float]) -> List[str]:
        if len(prices) < 2:
            return []
        signals: List[str] = []
        for idx in range(1, len(prices)):
            signals.append(self.generate_signal(prices[idx], prices[idx - 1]))
        return signals
