from lifeforce.agents.meta_cognition import MetaCognitionTool, ThinkingQuality
from lifeforce.agents.thinker import ThinkerAgent
from lifeforce.core.budget import BudgetGuard
from lifeforce.core.memory import MemorySystem


class MockConfig:
    pass


def test_meta_cognition_quality_assessment() -> None:
    tool = MetaCognitionTool()
    thought = "首先分析本质原因。其次建立相关联系。最后得到关键洞察。"
    observation = tool.observe_thinking_process(thought, {"time_taken": 1.2})
    assessment = tool.assess_thought_quality(observation)
    assert assessment.quality in {
        ThinkingQuality.EXCELLENT,
        ThinkingQuality.GOOD,
        ThinkingQuality.ACCEPTABLE,
        ThinkingQuality.POOR,
    }
    assert observation.is_deep is True


def test_thinker_meta_mode_refines_when_needed(tmp_path) -> None:
    memory = MemorySystem(str(tmp_path / "meta.db"))
    budget = BudgetGuard(hourly_limit=1000, daily_limit=10000, monthly_limit=100000)
    thinker = ThinkerAgent(memory=memory, budget_guard=budget, config=MockConfig())
    result = thinker.think("请反思今天的行为", mode="meta")
    assert isinstance(result, str)
    assert len(result) > 0
    memory.close()
