from pathlib import Path

from lifeforce.agents.thinker import ThinkerAgent
from lifeforce.core.budget import BudgetGuard
from lifeforce.core.memory import MemorySystem
from lifeforce.growth import GrowthEngine
from lifeforce.memory.self_model import SelfModelStore


class MockConfig:
    pass


def _build_engine(tmp_path: Path) -> GrowthEngine:
    memory = MemorySystem(str(tmp_path / "grow_inputs.db"), config={"data_dir": str(tmp_path)})
    budget = BudgetGuard(hourly_limit=2000, daily_limit=10000, monthly_limit=100000)
    thinker = ThinkerAgent(memory=memory, budget_guard=budget, config=MockConfig())
    self_model = SelfModelStore(tmp_path / "self_model")
    return GrowthEngine(data_root=tmp_path, memory=memory, thinker=thinker, self_model=self_model)


def test_collect_inputs_reads_five_pools(tmp_path: Path) -> None:
    (tmp_path / "creator_logs").mkdir(parents=True)
    (tmp_path / "system_logs").mkdir(parents=True)
    (tmp_path / "materials").mkdir(parents=True)
    (tmp_path / "self_outputs").mkdir(parents=True)
    (tmp_path / "env_changes").mkdir(parents=True)
    (tmp_path / "creator_logs" / "day1.md").write_text("creator decision", encoding="utf-8")
    (tmp_path / "system_logs" / "run.log").write_text("pytest ok", encoding="utf-8")
    (tmp_path / "materials" / "a.txt").write_text("complexity article", encoding="utf-8")
    (tmp_path / "self_outputs" / "best.txt").write_text("best answer", encoding="utf-8")
    (tmp_path / "env_changes" / "diff.txt").write_text("config changed", encoding="utf-8")

    engine = _build_engine(tmp_path)
    inputs = engine.collect_inputs()
    data = inputs.to_dict()
    assert data["creator_logs"]
    assert data["system_logs"]
    assert data["materials"]
    assert data["self_outputs"]
    assert data["env_changes"]
    engine.memory.close()
