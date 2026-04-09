from lifeforce.thinking_tools.analogy import AnalogyTool
from lifeforce.thinking_tools.base import ThinkingTool
from lifeforce.thinking_tools.first_principles import FirstPrinciplesTool
from lifeforce.thinking_tools.intentional_stance import IntentionalStanceTool
from lifeforce.thinking_tools.inversion import InversionTool

THINKING_TOOLS: dict[str, ThinkingTool] = {
    "first_principles": FirstPrinciplesTool(),
    "intentional_stance": IntentionalStanceTool(),
    "inversion": InversionTool(),
    "analogy": AnalogyTool(),
}


def get_tool(name: str) -> ThinkingTool | None:
    return THINKING_TOOLS.get(name)


def list_tools() -> list[str]:
    return sorted(THINKING_TOOLS.keys())
