"""Skill 基类。"""

from abc import ABC, abstractmethod
from typing import Any, Dict

from lifeforce.utils.logger import setup_logger


class Skill(ABC):
    """所有 Skill 的基类。"""

    def __init__(self, name: str) -> None:
        self.name = name
        self.logger = setup_logger(f"Skill.{name}")

    @abstractmethod
    def execute(self, params: Dict[str, Any]) -> Any:
        """执行 Skill。"""

    def run(self, payload: Dict[str, Any]) -> Any:
        """兼容旧接口。"""
        return self.execute(payload)
