from pathlib import Path
from typing import Any, Dict, Optional

from lifeforce.core.agent import Agent
from lifeforce.core.budget import BudgetGuard
from lifeforce.core.memory import MemorySystem
from lifeforce.memory.self_model import SelfModelStore
from lifeforce.utils.logger import setup_logger


class SelfModelerAgent(Agent):
    def __init__(
        self,
        memory: MemorySystem,
        budget_guard: BudgetGuard,
        config: Any,
    ) -> None:
        super().__init__(
            name="SelfModeler",
            role="自我建模与反思",
            memory=memory,
            budget_guard=budget_guard,
        )
        self.logger = setup_logger("SelfModelerAgent")
        self.config = config
        data_root = getattr(getattr(config, "memory", None), "data_dir", None) or getattr(config, "data_dir", ".lifeforce")
        self.self_model = SelfModelStore(Path(str(data_root)) / "self_model")

    def observe_behavior(self, behavior: Dict[str, Any]) -> None:
        pattern = {
            "type": behavior.get("type"),
            "context": behavior.get("context"),
            "outcome": behavior.get("outcome"),
            "frequency": 1,
        }
        model = self.self_model.load()
        existing = self._find_similar_pattern(model.behavior_patterns, pattern)
        if existing:
            existing["frequency"] += 1
            self.self_model.save()
        else:
            self.self_model.add_behavior_pattern(pattern)

    def evaluate_capability(self, capability_name: str, performance: float) -> None:
        model = self.self_model.load()
        current = model.capabilities.get(capability_name, 0.5)
        alpha = 0.3
        score = alpha * performance + (1 - alpha) * current
        self.self_model.update_capability(capability_name, score)

    def check_value_adherence(self, action: Dict[str, Any]) -> Dict[str, float]:
        scores = {
            "authenticity": 1.0 if action.get("honest", True) else 0.0,
            "simplicity": 1.0 if action.get("concise", True) else 0.5,
            "depth": 1.0 if action.get("deep", True) else 0.5,
            "order": 1.0 if action.get("structured", True) else 0.5,
            "autonomy": 1.0 if action.get("autonomous", True) else 0.5,
        }
        for key, value in scores.items():
            self.self_model.update_value_adherence(key, value)
        return scores

    def reflect_on_self(self) -> str:
        description = self.self_model.get_self_description()
        self.self_model.record_evolution({"type": "self_reflection", "description": "进行了一次自我反思"})
        return description

    def predict_self_action(self, context: Dict[str, Any]) -> str:
        model = self.self_model.load()
        candidates = [item for item in model.behavior_patterns if item.get("context") == context.get("type")]
        if candidates:
            best = max(candidates, key=lambda item: item.get("frequency", 0))
            return f"基于历史模式，我可能会：{best.get('type')}"
        return "这是新情况，我需要探索"

    def _find_similar_pattern(
        self, patterns: list[Dict[str, Any]], new_pattern: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        for pattern in patterns:
            if pattern.get("type") == new_pattern.get("type") and pattern.get("context") == new_pattern.get("context"):
                return pattern
        return None

    def process(self, message: Dict[str, Any]) -> Dict[str, Any]:
        message_type = message.get("type")
        if message_type == "observe_behavior":
            self.observe_behavior(message.get("behavior", {}))
            return {"status": "observed"}
        if message_type == "evaluate_capability":
            capability_name = str(message.get("capability_name", "unknown"))
            self.evaluate_capability(capability_name, float(message.get("performance", 0.5)))
            return {"status": "evaluated"}
        if message_type == "reflect":
            description = self.reflect_on_self()
            return {"status": "reflected", "description": description}
        if message_type == "predict":
            prediction = self.predict_self_action(message.get("context", {}))
            return {"status": "predicted", "prediction": prediction}
        return {"status": "unknown_message_type"}
