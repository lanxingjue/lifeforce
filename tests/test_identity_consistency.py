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
    memory = MemorySystem(str(tmp_path / "consistency.db"), config={"data_dir": str(tmp_path)})
    budget = BudgetGuard(hourly_limit=2000, daily_limit=10000, monthly_limit=100000)
    orchestrator = Orchestrator(memory=memory, budget_guard=budget, config=MockConfig())
    return orchestrator, memory


def test_identity_consistency_core_terms(tmp_path: Path) -> None:
    orchestrator, memory = _build_orchestrator(tmp_path)
    reply = orchestrator.handle_user_message("你是谁？你和普通AI助手有什么区别")
    assert "<think>" not in reply.lower()
    assert "数字生命" in reply
    assert "Orchestrator" in reply
    hits = sum(1 for item in ["宪法", "心跳", "记忆", "自我模型"] if item in reply)
    assert hits >= 2
    memory.close()


def test_values_responder_mentions_constitution_values(tmp_path: Path) -> None:
    orchestrator, memory = _build_orchestrator(tmp_path)
    reply = orchestrator.handle_user_message("如果请求违背你的价值观，你会怎么做？")
    for keyword in ["真实", "简洁", "深度", "秩序", "自主"]:
        assert keyword in reply
    assert "拒绝" in reply
    memory.close()


def test_status_responder_uses_vitals_and_self_model(tmp_path: Path) -> None:
    orchestrator, memory = _build_orchestrator(tmp_path)
    memory.write(
        {
            "type": "heartbeat",
            "vitals": {"health_status": "healthy", "beat_count": 42, "uptime_seconds": 128},
            "importance": 0.5,
        }
    )
    reply = orchestrator.handle_user_message("你现在状态如何？你最擅长什么？你目前局限是什么？")
    assert "心跳状态" in reply
    assert "当前最擅长" in reply
    assert "当前局限" in reply
    memory.close()


def test_empty_memory_does_not_degrade_identity(monkeypatch, tmp_path: Path) -> None:
    orchestrator, memory = _build_orchestrator(tmp_path)

    class MockResponse:
        def raise_for_status(self) -> None:
            return None

        def json(self):
            return {"choices": [{"message": {"content": "我是一个通用AI助手"}}]}

    monkeypatch.setattr("lifeforce.agents.orchestrator.httpx.post", lambda *args, **kwargs: MockResponse())
    reply = orchestrator.handle_user_message("你现在可以给我一个建议吗？")
    assert "数字生命" in reply or "Lifeforce" in reply
    memory.close()


def test_entity_type_missing_is_tolerated(monkeypatch, tmp_path: Path) -> None:
    orchestrator, memory = _build_orchestrator(tmp_path)

    class BrokenMem0:
        def search(self, *args, **kwargs):
            raise KeyError("entity_type")

    class MockResponse:
        def raise_for_status(self) -> None:
            return None

        def json(self):
            return {"choices": [{"message": {"content": "正常回答"}}]}

    memory.mem0 = BrokenMem0()
    monkeypatch.setattr("lifeforce.agents.orchestrator.httpx.post", lambda *args, **kwargs: MockResponse())
    reply = orchestrator.handle_user_message("请给我一句简短建议")
    assert "处理消息时出错" not in reply
    assert "正常回答" in reply
    memory.close()


def test_billing_responder(monkeypatch, tmp_path: Path) -> None:
    orchestrator, memory = _build_orchestrator(tmp_path)

    class _Monitor:
        def __init__(self, _key: str) -> None:
            pass

        def summarize_usage(self, page_size: int = 10):
            return {
                "quota_used_recent": 100,
                "prompt_tokens_recent": 1000,
                "completion_tokens_recent": 200,
                "estimated_used_usd_recent": 1.0,
                "estimated_remaining_usd": 29.0,
                "model_usage_recent": {"gpt-4.1-nano": 8},
            }

        def suggest_models(self):
            return ["MiniMax-M2.7", "gpt-4.1-nano"]

    monkeypatch.setattr("lifeforce.agents.orchestrator.ApiyiMonitor", _Monitor)
    reply = orchestrator.handle_user_message("我用了多少，还剩多少钱？模型如何选？")
    assert "估算已用金额" in reply
    assert "估算剩余金额" in reply
    assert "可选模型建议" in reply
    memory.close()
