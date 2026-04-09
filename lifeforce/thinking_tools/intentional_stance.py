from typing import Any, Dict

from lifeforce.thinking_tools.base import ThinkingTool


class IntentionalStanceTool(ThinkingTool):
    def __init__(self) -> None:
        super().__init__(
            name="intentional_stance",
            description="意向立场：把系统当作有目标与信念的主体来建模",
            when_to_use="需要预测系统/个体行为或博弈互动时",
        )

    def apply(self, problem: str, context: Dict[str, Any] | None = None) -> str:
        actor = (context or {}).get("actor", "目标系统")
        return (
            f"[意向立场]\n问题：{problem}\n"
            f"对象：{actor}\n"
            "1. 它想要什么？（目标函数）\n"
            "2. 它相信什么？（信息与认知模型）\n"
            "3. 在这些目标与信念下，它最可能如何行动？"
        )
