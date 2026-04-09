from typing import Any, Dict

from lifeforce.thinking_tools.base import ThinkingTool


class FirstPrinciplesTool(ThinkingTool):
    def __init__(self) -> None:
        super().__init__(
            name="first_principles",
            description="第一性原理：把问题拆到基本事实再重构",
            when_to_use="问题复杂、存在惯性假设、需要重构解法时",
        )

    def apply(self, problem: str, context: Dict[str, Any] | None = None) -> str:
        assumptions = (context or {}).get("assumptions", "列出你当前默认的假设")
        return (
            f"[第一性原理]\n问题：{problem}\n"
            f"1. 识别假设：{assumptions}\n"
            "2. 分解到基本事实：哪些是不可再简化、可验证的事实？\n"
            "3. 重新推导：不依赖原路径，从基本事实出发构建新方案。"
        )
