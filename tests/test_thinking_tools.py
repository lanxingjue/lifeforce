from pathlib import Path

from lifeforce.agents.thinker import ThinkerAgent
from lifeforce.core.budget import BudgetGuard
from lifeforce.core.memory import MemorySystem
from lifeforce.thinking_tools import get_tool, list_tools


class MockConfig:
    pass


def test_tool_registry() -> None:
    tools = list_tools()
    assert tools == ["analogy", "first_principles", "intentional_stance", "inversion"]
    assert get_tool("first_principles") is not None


def test_thinker_select_tool_and_apply(tmp_path: Path) -> None:
    memory = MemorySystem(str(tmp_path / "tools.db"))
    budget = BudgetGuard(hourly_limit=1000, daily_limit=10000, monthly_limit=100000)
    thinker = ThinkerAgent(memory=memory, budget_guard=budget, config=MockConfig())
    selected = thinker.select_thinking_tool("如何避免这个方案失败")
    assert selected == "inversion"
    thought = thinker.think_with_tool("如何避免这个方案失败", selected, context={})
    assert "[反向思考]" in thought
    memory.close()
