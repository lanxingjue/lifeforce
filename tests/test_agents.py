from pathlib import Path
import sys

import pytest

from lifeforce.agents.executor import ExecutorAgent
from lifeforce.agents.observer import ObserverAgent
from lifeforce.core.budget import BudgetGuard
from lifeforce.core.memory import MemorySystem


@pytest.fixture
def memory() -> MemorySystem:
    db_path = Path(".lifeforce/test_memory.db")
    db_path.parent.mkdir(exist_ok=True)
    mem = MemorySystem(str(db_path))
    yield mem
    mem.close()
    db_path.unlink(missing_ok=True)


@pytest.fixture
def budget_guard() -> BudgetGuard:
    return BudgetGuard(hourly_limit=1000, daily_limit=10000, monthly_limit=100000)


class MockConfig:
    class LLM:
        model = "MiniMax-M2.7"
        base_url = "https://api.apiyi.com/v1"
        api_key = "test-key"

    llm = LLM()
    skills = {"shell_exec": {"safety_check": False}}


def test_observer_records_file_change(memory: MemorySystem, budget_guard: BudgetGuard) -> None:
    observer = ObserverAgent(memory, budget_guard)
    observer.handle_file_change("created", "demo.txt")
    changes = observer.process({"command": "get_recent_changes", "limit": 5})
    assert changes["changes"]
    assert changes["changes"][0]["type"] == "file_change"


def test_executor_shell_exec(memory: MemorySystem, budget_guard: BudgetGuard) -> None:
    executor = ExecutorAgent(memory, budget_guard, MockConfig())
    cmd = f'"{sys.executable}" --version'
    result = executor.execute_shell(cmd, require_approval=False)
    assert result["status"] == "success"
    assert result["result"]["returncode"] == 0
    combined_output = (result["result"]["stdout"] + result["result"]["stderr"]).lower()
    assert "python" in combined_output


def test_executor_unknown_skill(memory: MemorySystem, budget_guard: BudgetGuard) -> None:
    executor = ExecutorAgent(memory, budget_guard, MockConfig())
    result = executor.process({"skill": "unknown", "params": {}})
    assert "error" in result


def test_executor_select_skills_with_chaos_edge(memory: MemorySystem, budget_guard: BudgetGuard) -> None:
    executor = ExecutorAgent(memory, budget_guard, MockConfig())
    selected = executor.select_skills({"intent": "请调用 llm 生成回复"})
    assert selected
    assert all(item in executor.skills for item in selected)

