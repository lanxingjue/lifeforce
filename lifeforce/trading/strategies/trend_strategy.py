"""趋势跟踪策略。"""

from dataclasses import dataclass
from typing import List, Tuple

import numpy as np


@dataclass
class TrendStrategy:
    fast_window: int = 5
    slow_window: int = 20

    def moving_averages(self, prices: List[float]) -> Tuple[float, float]:
        if len(prices) < self.slow_window:
            return 0.0, 0.0
        arr = np.array(prices, dtype=float)
        fast = float(arr[-self.fast_window :].mean())
        slow = float(arr[-self.slow_window :].mean())
        return fast, slow

    def signal(self, prices: List[float]) -> str:
        if len(prices) < self.slow_window + 1:
            return "hold"
        prev_fast, prev_slow = self.moving_averages(prices[:-1])
        curr_fast, curr_slow = self.moving_averages(prices)
        if prev_fast <= prev_slow and curr_fast > curr_slow:
            return "buy"
        if prev_fast >= prev_slow and curr_fast < curr_slow:
            return "sell"
        return "hold"
