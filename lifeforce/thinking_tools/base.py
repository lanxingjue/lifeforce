from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict


@dataclass
class ThinkingTool(ABC):
    name: str
    description: str
    when_to_use: str

    @abstractmethod
    def apply(self, problem: str, context: Dict[str, Any] | None = None) -> str:
        raise NotImplementedError
