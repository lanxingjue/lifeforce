from typing import Any, Dict

from lifeforce.thinking_tools.base import ThinkingTool


class AnalogyTool(ThinkingTool):
    def __init__(self) -> None:
        super().__init__(
            name="analogy",
            description="类比推理：从结构相似的问题迁移策略",
            when_to_use="当前问题信息不足、但存在可借鉴领域经验时",
        )

    def apply(self, problem: str, context: Dict[str, Any] | None = None) -> str:
        reference_domain = (context or {}).get("reference_domain", "一个结构相似的历史案例")
        return (
            f"[类比推理]\n问题：{problem}\n"
            f"参考域：{reference_domain}\n"
            "1. 当前问题与参考问题的结构相似点是什么？\n"
            "2. 哪些解法可迁移，哪些边界不可迁移？\n"
            "3. 形成最小可验证的迁移方案并快速验证。"
        )
