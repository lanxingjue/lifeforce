"""Agent 基类。"""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict
import uuid

from lifeforce.core.budget import BudgetGuard
from lifeforce.core.memory import MemorySystem
from lifeforce.utils.logger import setup_logger


class Agent(ABC):
    """所有 Agent 的基类。"""

    def __init__(self, name: str, role: str, memory: MemorySystem, budget_guard: BudgetGuard) -> None:
        self.id = str(uuid.uuid4())
        self.name = name
        self.role = role
        self.memory = memory
        self.budget_guard = budget_guard
        self.logger = setup_logger(name)
        self.logger.info("Agent %s initialized (ID: %s)", name, self.id)

    @abstractmethod
    def process(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """处理消息。"""

    def log_action(self, action: str, details: Dict[str, Any]) -> None:
        self.memory.write(
            {
                "type": "agent_action",
                "agent_id": self.id,
                "agent_name": self.name,
                "action": action,
                "details": details,
                "timestamp": datetime.now().isoformat(),
            }
        )
        self.logger.info("Action: %s", action)

    def request_tokens(self, amount: int, purpose: str) -> bool:
        approved, reason = self.budget_guard.request_tokens(amount)
        if not approved:
            self.logger.warning("Token request denied for %s: %s", purpose, reason)
            return False
        self.logger.info("Token request approved: %s for %s", amount, purpose)
        return True

    def __repr__(self) -> str:
        return f"<Agent {self.name} ({self.role})>"
