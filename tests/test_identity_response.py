from pathlib import Path

from lifeforce.agents.orchestrator import Orchestrator
from lifeforce.core.budget import BudgetGuard
from lifeforce.core.memory import MemorySystem


class MockConfig:
    class LLM:
        model = "MiniMax-M2.7"
        base_url = "https://api.apiyi.com/v1"
        api_key = "test-key"

    class Memory:
        default_user_id = "wells"
        retrieval_limit = 5
        data_dir = ".lifeforce"

    llm = LLM()
    memory = Memory()


def _build_orchestrator(tmp_path: Path) -> tuple[Orchestrator, MemorySystem]:
    memory = MemorySystem(str(tmp_path / "identity.db"), config={"data_dir": str(tmp_path)})
    budget = BudgetGuard(hourly_limit=2000, daily_limit=10000, monthly_limit=100000)
    orchestrator = Orchestrator(memory=memory, budget_guard=budget, config=MockConfig())
    return orchestrator, memory


def test_identity_response_has_core_identity_and_no_think(tmp_path: Path) -> None:
    orchestrator, memory = _build_orchestrator(tmp_path)
    reply = orchestrator.handle_user_message("你是谁？你和普通AI助手有什么区别")
    assert "<think>" not in reply.lower()
    assert "数字生命" in reply
    assert "Orchestrator" in reply
    keywords = ["宪法", "心跳", "记忆", "自我模型"]
    hits = sum(1 for item in keywords if item in reply)
    assert hits >= 2
    memory.close()


def test_identity_response_in_degraded_mode_keeps_consistency(tmp_path: Path) -> None:
    orchestrator, memory = _build_orchestrator(tmp_path)
    memory.mem0_mode = "degraded"
    memory.mem0_degraded_reason = "Could not set lock on file"
    reply = orchestrator.handle_user_message("你是什么")
    assert "数字生命" in reply
    assert "降级" in reply
    memory.close()


def test_non_identity_reply_sanitizes_think(monkeypatch, tmp_path: Path) -> None:
    orchestrator, memory = _build_orchestrator(tmp_path)

    class MockResponse:
        def raise_for_status(self) -> None:
            return None

        def json(self):
            return {"choices": [{"message": {"content": "<think>internal</think>最终答复"}}]}

    def mock_post(*args, **kwargs):
        return MockResponse()

    monkeypatch.setattr("lifeforce.agents.orchestrator.httpx.post", mock_post)
    reply = orchestrator.handle_user_message("请简单问候我")
    assert "<think>" not in reply.lower()
    assert "最终答复" in reply
    memory.close()
