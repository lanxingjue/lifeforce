"""元认知工具。"""

from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List


class ThinkingQuality(Enum):
    """思考质量评估等级。"""

    EXCELLENT = "excellent"
    GOOD = "good"
    ACCEPTABLE = "acceptable"
    POOR = "poor"


@dataclass
class ThoughtObservation:
    """对思考过程的观察结果。"""

    thought_content: str
    reasoning_steps: List[str]
    assumptions_made: List[str]
    confidence_level: float
    time_taken: float
    is_deep: bool = False
    is_structured: bool = False
    has_connections: bool = False
    has_insights: bool = False


@dataclass
class QualityAssessment:
    """思考质量评估。"""

    quality: ThinkingQuality
    strengths: List[str]
    weaknesses: List[str]
    suggestions: List[str]
    needs_improvement: bool


class MetaCognitionTool:
    """用于观察、评估、改进思考过程的元认知工具。"""

    def observe_thinking_process(self, thought: str, context: Dict[str, Any]) -> ThoughtObservation:
        """观察思考过程并提取元信息。"""
        reasoning_steps = self._extract_reasoning_steps(thought)
        assumptions = self._identify_assumptions(thought)
        confidence = self._estimate_confidence(thought, context)
        return ThoughtObservation(
            thought_content=thought,
            reasoning_steps=reasoning_steps,
            assumptions_made=assumptions,
            confidence_level=confidence,
            time_taken=float(context.get("time_taken", 0.0)),
            is_deep=self._check_depth(thought),
            is_structured=self._check_structure(thought),
            has_connections=self._check_connections(thought),
            has_insights=self._check_insights(thought),
        )

    def assess_thought_quality(self, observation: ThoughtObservation) -> QualityAssessment:
        """评估思考质量并给出改进建议。"""
        strengths: List[str] = []
        weaknesses: List[str] = []
        suggestions: List[str] = []

        if observation.is_deep:
            strengths.append("思考有深度，触及本质")
        else:
            weaknesses.append("思考较浅，停留在表面")
            suggestions.append("尝试追问'为什么'，深入一层")

        if observation.is_structured:
            strengths.append("思考有结构，层次清晰")
        else:
            weaknesses.append("思考较散乱，缺乏组织")
            suggestions.append("使用框架整理思路")

        if observation.has_connections:
            strengths.append("建立了知识连接")
        else:
            weaknesses.append("孤立思考，未建立连接")
            suggestions.append("尝试关联已有知识")

        if observation.has_insights:
            strengths.append("产生了新洞察")
        else:
            suggestions.append("尝试从不同角度思考")

        if observation.confidence_level < 0.5:
            weaknesses.append(f"置信度较低 ({observation.confidence_level:.0%})")
            suggestions.append("需要更多证据或推理")

        quality = self._determine_quality(strengths, weaknesses)
        return QualityAssessment(
            quality=quality,
            strengths=strengths,
            weaknesses=weaknesses,
            suggestions=suggestions,
            needs_improvement=quality in {ThinkingQuality.POOR, ThinkingQuality.ACCEPTABLE},
        )

    def refine_thought(self, thought: str, assessment: QualityAssessment) -> str:
        """按评估建议改进思考文本。"""
        if not assessment.needs_improvement:
            return thought
        refined = thought
        suggestions = " | ".join(assessment.suggestions)
        if "深入一层" in suggestions:
            refined += "\n\n[深入思考] 追问本质原因..."
        if "使用框架整理思路" in suggestions:
            refined = self._restructure_thought(refined)
        if "关联已有知识" in suggestions:
            refined += "\n\n[建立连接] 这让我想到..."
        return refined

    def _extract_reasoning_steps(self, thought: str) -> List[str]:
        lines = thought.splitlines()
        return [line.strip() for line in lines if line.strip()][:5]

    def _identify_assumptions(self, thought: str) -> List[str]:
        keywords = ("假设", "如果", "假定", "前提")
        return [line.strip() for line in thought.splitlines() if any(keyword in line for keyword in keywords)]

    def _estimate_confidence(self, thought: str, _context: Dict[str, Any]) -> float:
        confidence = 0.7
        if "不确定" in thought or "可能" in thought:
            confidence -= 0.2
        if "肯定" in thought or "确定" in thought:
            confidence += 0.1
        return max(0.0, min(1.0, confidence))

    def _check_depth(self, thought: str) -> bool:
        indicators = ("本质", "根本", "为什么", "原因", "机制")
        return any(indicator in thought for indicator in indicators)

    def _check_structure(self, thought: str) -> bool:
        indicators = ("首先", "其次", "然后", "最后", "第一", "第二")
        return any(indicator in thought for indicator in indicators)

    def _check_connections(self, thought: str) -> bool:
        indicators = ("类似", "相关", "联系", "对比", "就像")
        return any(indicator in thought for indicator in indicators)

    def _check_insights(self, thought: str) -> bool:
        indicators = ("发现", "意识到", "原来", "洞察", "关键")
        return any(indicator in thought for indicator in indicators)

    def _determine_quality(self, strengths: List[str], weaknesses: List[str]) -> ThinkingQuality:
        score = len(strengths) - len(weaknesses)
        if score >= 3:
            return ThinkingQuality.EXCELLENT
        if score >= 1:
            return ThinkingQuality.GOOD
        if score >= -1:
            return ThinkingQuality.ACCEPTABLE
        return ThinkingQuality.POOR

    def _restructure_thought(self, thought: str) -> str:
        return (
            "[结构化思考]\n"
            "1. 问题分析\n"
            f"{thought}\n\n"
            "2. 关键洞察\n"
            "...\n\n"
            "3. 结论\n"
            "..."
        )
