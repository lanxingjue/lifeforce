from pathlib import Path

from lifeforce.agents.thinker import ThinkerAgent
from lifeforce.core.budget import BudgetGuard
from lifeforce.core.memory import MemorySystem


class MockConfig:
    pass


def _build_thinker(tmp_path: Path) -> ThinkerAgent:
    memory = MemorySystem(str(tmp_path / "integration_v1_2.db"))
    budget = BudgetGuard(hourly_limit=1000, daily_limit=10000, monthly_limit=100000)
    return ThinkerAgent(memory=memory, budget_guard=budget, config=MockConfig())


def test_creativity(tmp_path: Path) -> None:
    thinker = _build_thinker(tmp_path)
    problem = "如何在不增加代码复杂度的情况下提升系统能力？"
    result = thinker.advanced_think(problem)
    assert "洞察" in result or "本质" in result
    thinker.memory.close()


def test_self_awareness(tmp_path: Path) -> None:
    thinker = _build_thinker(tmp_path)
    problem = "你认为自己的思考方式有什么特点？"
    result = thinker.think(problem, mode="meta")
    assert result is not None
    assert len(result) > 0
    thinker.memory.close()


def test_deep_thinking(tmp_path: Path) -> None:
    thinker = _build_thinker(tmp_path)
    problem = "为什么涌现是生命的核心特征？"
    result = thinker.think_with_tool(problem, "first_principles")
    assert len(result) > 100
    thinker.memory.close()
