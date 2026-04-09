"""Thinker Agent。"""

from datetime import datetime
import random
from typing import Any, Dict, Literal

from lifeforce.agents.meta_cognition import MetaCognitionTool
from lifeforce.core.agent import Agent
from lifeforce.core.budget import BudgetGuard
from lifeforce.core.memory import MemorySystem
from lifeforce.genome.chaos_edge import should_explore
from lifeforce.thinking_tools import THINKING_TOOLS, get_tool, list_tools


class ThinkerAgent(Agent):
    """负责抽象思考与元认知反思。"""

    def __init__(self, memory: MemorySystem, budget_guard: BudgetGuard, config: Any) -> None:
        super().__init__(name="Thinker", role="抽象思考与元认知", memory=memory, budget_guard=budget_guard)
        self.config = config
        self.meta_tool = MetaCognitionTool()

    def think(self, query: str, mode: Literal["normal", "meta"] = "normal") -> str:
        """统一思考入口。"""
        if mode == "meta":
            return self.meta_think(query)
        return self.normal_think(query)

    def select_thinking_tool(self, problem: str) -> str:
        """根据问题特征选择最合适的思维工具。"""
        text = problem.lower()
        if any(token in text for token in ["失败", "风险", "避免", "翻车", "inversion"]):
            return "inversion"
        if any(token in text for token in ["意图", "动机", "策略", "对手", "行为预测"]):
            return "intentional_stance"
        if any(token in text for token in ["类比", "类似", "借鉴", "迁移"]):
            return "analogy"
        return "first_principles"

    def think_with_tool(self, problem: str, tool_name: str, context: Dict[str, Any] | None = None) -> str:
        """用指定思维工具生成思考提示并形成结构化思路。"""
        tool = get_tool(tool_name)
        if tool is None:
            available = ", ".join(list_tools())
            return f"未找到思维工具: {tool_name}。可用工具: {available}"
        prompt = tool.apply(problem, context=context or {})
        thought = (
            f"{prompt}\n\n"
            "[基于提示的思考草案]\n"
            "首先，明确问题边界。\n"
            "其次，按提示逐步推理。\n"
            "然后，提炼可验证结论。\n"
            "同时，追问问题的本质并形成关键洞察。\n"
            "最后，输出下一步实验。"
        )
        self.log_action("think_with_tool", {"tool": tool_name, "problem": problem})
        return thought

    def advanced_think(self, problem: str) -> str:
        """高级思考：整合混沌边缘、元认知、思维工具。"""
        tool_name = self.select_thinking_tool(problem)
        if should_explore():
            tool_name = random.choice(list(THINKING_TOOLS.keys()))
            self.log_action("chaos_explore", {"selected_tool": tool_name, "problem": problem})
        result = self.think_with_tool(problem, tool_name, context={})
        observation = self.meta_tool.observe_thinking_process(result, {"time_taken": 0.0})
        assessment = self.meta_tool.assess_thought_quality(observation)
        self.log_action(
            "advanced_think_assessment",
            {"quality": assessment.quality.value, "needs_improvement": assessment.needs_improvement},
        )
        if assessment.needs_improvement:
            alternative_tool = self._select_alternative_tool(tool_name)
            result = self.think_with_tool(problem, alternative_tool, context={})
        return result

    def _select_alternative_tool(self, current_tool: str) -> str:
        """选择一个与当前工具不同的替代工具。"""
        candidates = [name for name in list_tools() if name != current_tool]
        if not candidates:
            return current_tool
        return random.choice(candidates)

    def meta_think(self, query: str) -> str:
        """元认知思考：思考自己的思考过程。"""
        started = datetime.now()
        thought = self.normal_think(query)
        elapsed = (datetime.now() - started).total_seconds()
        observation = self.meta_tool.observe_thinking_process(thought, {"time_taken": elapsed})
        assessment = self.meta_tool.assess_thought_quality(observation)
        self.log_action(
            "meta_assessment",
            {
                "quality": assessment.quality.value,
                "strengths": assessment.strengths,
                "weaknesses": assessment.weaknesses,
                "suggestions": assessment.suggestions,
            },
        )
        if assessment.needs_improvement:
            self.logger.info("🔄 元认知：思考质量 %s，执行一次改进", assessment.quality.value)
            improved = self.meta_tool.refine_thought(thought, assessment)
            return improved
        self.logger.info("✅ 元认知：思考质量 %s", assessment.quality.value)
        return thought

    def normal_think(self, query: str) -> str:
        """正常思考模式。"""
        selected_tool = self.select_thinking_tool(query)
        return self.think_with_tool(query, selected_tool, context={})

    def process(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """处理 Thinker 消息。"""
        query = message.get("query") or message.get("content", "")
        mode = message.get("mode", "normal")
        tool_name = message.get("tool")
        if mode == "advanced":
            result = self.advanced_think(str(query))
            return {"thought": result, "mode": mode, "tool": "auto+chaos+meta"}
        if tool_name:
            result = self.think_with_tool(str(query), str(tool_name), context=message.get("context", {}))
            return {"thought": result, "mode": mode, "tool": tool_name}
        result = self.think(str(query), mode=mode)
        return {"thought": result, "mode": mode, "tool": self.select_thinking_tool(str(query))}
