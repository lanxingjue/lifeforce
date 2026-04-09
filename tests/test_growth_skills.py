from pathlib import Path

from lifeforce.agents.thinker import ThinkerAgent
from lifeforce.core.budget import BudgetGuard
from lifeforce.core.memory import MemorySystem
from lifeforce.growth import GrowthEngine
from lifeforce.memory.self_model import SelfModelStore


class MockConfig:
    pass


def test_skill_search_and_install_updates_self_model(tmp_path: Path) -> None:
    memory = MemorySystem(str(tmp_path / "grow_skill.db"), config={"data_dir": str(tmp_path)})
    budget = BudgetGuard(hourly_limit=2000, daily_limit=10000, monthly_limit=100000)
    thinker = ThinkerAgent(memory=memory, budget_guard=budget, config=MockConfig())
    self_model = SelfModelStore(tmp_path / "self_model")
    engine = GrowthEngine(data_root=tmp_path, memory=memory, thinker=thinker, self_model=self_model)

    skills = engine.skill_manager.search("图片生成", limit=3)
    assert skills
    installed = engine.skill_manager.install(skills[0]["id"])
    model = self_model.load()

    assert installed["id"] == skills[0]["id"]
    current = model.growth_profile["capabilities"]["current"]
    assert installed["name"] in current
    memory.close()
