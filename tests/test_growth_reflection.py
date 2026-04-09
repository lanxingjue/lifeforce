from pathlib import Path

from lifeforce.agents.thinker import ThinkerAgent
from lifeforce.core.budget import BudgetGuard
from lifeforce.core.memory import MemorySystem
from lifeforce.growth import GrowthEngine
from lifeforce.memory.self_model import SelfModelStore


class MockConfig:
    pass


def test_reflect_deep_updates_self_model(tmp_path: Path) -> None:
    memory = MemorySystem(str(tmp_path / "grow_reflect.db"), config={"data_dir": str(tmp_path)})
    budget = BudgetGuard(hourly_limit=2000, daily_limit=10000, monthly_limit=100000)
    thinker = ThinkerAgent(memory=memory, budget_guard=budget, config=MockConfig())
    self_model = SelfModelStore(tmp_path / "self_model")
    engine = GrowthEngine(data_root=tmp_path, memory=memory, thinker=thinker, self_model=self_model)
    inputs = engine.collect_inputs()
    reflection = engine.reflect_deep(inputs)
    model = self_model.load()

    assert "明日策略" in reflection["text"]
    assert model.growth_profile["evolution_count"] >= 1
    assert model.growth_profile["last_reflection"] is not None
    assert model.growth_profile["limitations"]["current"]
    assert model.growth_profile["next_strategy"]
    memory.close()
