from typing import Any, Dict

from lifeforce.thinking_tools.base import ThinkingTool


class InversionTool(ThinkingTool):
    def __init__(self) -> None:
        super().__init__(
            name="inversion",
            description="反向思考：从失败路径反推成功约束",
            when_to_use="目标不清晰或风险较高、需要规避灾难性失败时",
        )

    def apply(self, problem: str, context: Dict[str, Any] | None = None) -> str:
        return (
            f"[反向思考]\n问题：{problem}\n"
            "1. 若要彻底失败，最可能做错哪些事？\n"
            "2. 这些失败模式的早期信号是什么？\n"
            "3. 把失败清单转为约束与检查项，再定义正向行动。"
        )
