"""混沌边缘基因控制器。"""

from dataclasses import dataclass, field
import random
from typing import Any, Dict, List, Literal, Sequence

from lifeforce.utils.logger import setup_logger


@dataclass
class ChaosEdgeConfig:
    """混沌边缘配置。"""

    exploration_rate: float = 0.15
    temperature: Literal["low", "medium", "high"] = "medium"
    randomness_injection: bool = True
    TEMP_EXPLORATION: Dict[str, float] = field(
        default_factory=lambda: {
            "low": 0.05,
            "medium": 0.15,
            "high": 0.30,
        }
    )

    def effective_exploration_rate(self) -> float:
        """返回当前温度下的探索率。"""
        return self.TEMP_EXPLORATION.get(self.temperature, self.exploration_rate)


class ChaosEdgeController:
    """在探索与利用之间做动态平衡。"""

    def __init__(self, config: ChaosEdgeConfig | None = None) -> None:
        self.config = config or ChaosEdgeConfig()
        self.logger = setup_logger("ChaosEdgeController")
        self.total_decisions = 0
        self.explore_decisions = 0
        self.exploit_decisions = 0

    def should_explore(self) -> bool:
        """使用 epsilon-greedy 策略判断是否探索。"""
        self.total_decisions += 1
        epsilon = self.config.effective_exploration_rate()
        explore = random.random() < epsilon
        if explore:
            self.explore_decisions += 1
        else:
            self.exploit_decisions += 1
        self.logger.debug("Chaos decision explore=%s epsilon=%.3f", explore, epsilon)
        return explore

    def inject_randomness(self, candidates: Sequence[Any], top_k: int = 3) -> List[Any]:
        """在候选项中注入随机性，返回重排后的候选列表。"""
        if not candidates:
            return []
        if not self.config.randomness_injection:
            return list(candidates)

        pool = list(candidates)
        k = max(1, min(top_k, len(pool)))
        head = pool[:k]
        tail = pool[k:]
        if self.should_explore():
            random.shuffle(head)
            self.logger.info("Injected exploration randomness into %s candidates", len(head))
        return head + tail

    def adjust_temperature(self, context: str) -> Literal["low", "medium", "high"]:
        """根据上下文动态调温。"""
        text = (context or "").lower()
        if any(token in text for token in ["stuck", "局部最优", "重复", "deadlock"]):
            self.config.temperature = "high"
        elif any(token in text for token in ["critical", "稳定", "稳定性", "production", "线上"]):
            self.config.temperature = "low"
        else:
            self.config.temperature = "medium"
        self.logger.info("Chaos temperature adjusted to %s", self.config.temperature)
        return self.config.temperature

    def get_stats(self) -> Dict[str, Any]:
        """返回控制器统计信息。"""
        exploration_ratio = (
            self.explore_decisions / self.total_decisions if self.total_decisions > 0 else 0.0
        )
        return {
            "total_decisions": self.total_decisions,
            "explore_decisions": self.explore_decisions,
            "exploit_decisions": self.exploit_decisions,
            "exploration_ratio": exploration_ratio,
            "current_temperature": self.config.temperature,
            "effective_exploration_rate": self.config.effective_exploration_rate(),
            "randomness_injection": self.config.randomness_injection,
        }


_controller = ChaosEdgeController()


def get_chaos_edge_controller() -> ChaosEdgeController:
    """获取全局混沌边缘控制器。"""
    return _controller


def should_explore() -> bool:
    """全局探索判断函数。"""
    return _controller.should_explore()


def inject_randomness(candidates: Sequence[Any], top_k: int = 3) -> List[Any]:
    """全局随机性注入函数。"""
    return _controller.inject_randomness(candidates, top_k=top_k)


def adjust_temperature(context: str) -> Literal["low", "medium", "high"]:
    """全局温度调节函数。"""
    return _controller.adjust_temperature(context)


def get_chaos_stats() -> Dict[str, Any]:
    """全局统计查询函数。"""
    return _controller.get_stats()
