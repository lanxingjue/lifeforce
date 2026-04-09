"""预算管理系统。"""

from collections import defaultdict
from datetime import datetime, timedelta
from typing import Dict, Tuple

from lifeforce.utils.logger import setup_logger


class BudgetGuard:
    """防止 token 超预算。"""

    def __init__(self, hourly_limit: int = 100, daily_limit: int = 1000, monthly_limit: int = 10000) -> None:
        self.limits = {
            "hourly": hourly_limit,
            "daily": daily_limit,
            "monthly": monthly_limit,
        }
        self.usage = defaultdict(int)
        self.reset_times = {
            "hourly": datetime.now() + timedelta(hours=1),
            "daily": datetime.now() + timedelta(days=1),
            "monthly": datetime.now() + timedelta(days=30),
        }
        self.logger = setup_logger("BudgetGuard")

    def request_tokens(self, amount: int) -> Tuple[bool, str]:
        self._check_reset()
        for period, limit in self.limits.items():
            if self.usage[period] + amount > limit:
                return False, f"超过 {period} 限制 ({self.usage[period]}/{limit})"
        for period in self.limits:
            self.usage[period] += amount
        return True, "OK"

    def _check_reset(self) -> None:
        now = datetime.now()
        for period, reset_time in self.reset_times.items():
            if now >= reset_time:
                self.usage[period] = 0
                if period == "hourly":
                    self.reset_times[period] = now + timedelta(hours=1)
                elif period == "daily":
                    self.reset_times[period] = now + timedelta(days=1)
                else:
                    self.reset_times[period] = now + timedelta(days=30)

    def get_usage(self) -> Dict[str, Dict[str, float]]:
        self._check_reset()
        return {
            period: {
                "used": self.usage[period],
                "limit": self.limits[period],
                "remaining": self.limits[period] - self.usage[period],
                "percentage": (self.usage[period] / self.limits[period]) * 100,
            }
            for period in self.limits
        }
