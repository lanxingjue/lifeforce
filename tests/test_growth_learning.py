from pathlib import Path

from lifeforce.agents.thinker import ThinkerAgent
from lifeforce.core.budget import BudgetGuard
from lifeforce.core.memory import MemorySystem
from lifeforce.growth import GrowthEngine
from lifeforce.memory.self_model import SelfModelStore


class MockConfig:
    pass


def test_learning_pipeline_extracts_insights_and_writes_memory(tmp_path: Path) -> None:
    memory = MemorySystem(str(tmp_path / "grow_learning.db"), config={"data_dir": str(tmp_path)})
    budget = BudgetGuard(hourly_limit=2000, daily_limit=10000, monthly_limit=100000)
    thinker = ThinkerAgent(memory=memory, budget_guard=budget, config=MockConfig())
    self_model = SelfModelStore(tmp_path / "self_model")
    engine = GrowthEngine(data_root=tmp_path, memory=memory, thinker=thinker, self_model=self_model)

    result = engine.learning.learn_topic("混沌边缘", limit=2)
    learn_items = memory.read(memory_type="learning", limit=5)

    assert result["insights"]
    assert len(result["materials"]) == 2
    assert learn_items
    assert "混沌边缘" in str(learn_items[0]["content"])
    memory.close()
