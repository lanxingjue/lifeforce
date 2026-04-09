"""学习管道：搜索 -> 洞察 -> 记忆 -> 世界模型。"""

from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

from lifeforce.core.search_manager import SearchManager
from lifeforce.memory.world_model import WorldModel


def learning_pipeline(
    topic: str,
    memory: Any = None,
    vitals: Any = None,
    data_root: Path | None = None,
) -> Dict[str, Any]:
    _ = data_root
    world_model = WorldModel()
    search_manager = SearchManager(
        memory=memory,
        vitals=vitals,
        world_model=world_model,
        data_dir="data",
    )

    search_result = search_manager.search(query=topic, intent="learning", num_results=5)
    if not search_result.get("success", False):
        return {"topic": topic, "success": False, "error": search_result.get("error")}

    insights: List[Dict[str, Any]] = list(search_result.get("insights", []))
    search_manager.save_insights_to_memory(insights, topic)

    materials = [
        {"url": str(item.get("source", "")), "title": str(item.get("title", ""))}
        for item in insights[:3]
    ]
    if memory and hasattr(memory, "write"):
        memory.write(
            {
                "type": "learning",
                "content": {
                    "topic": topic,
                    "materials": materials,
                    "insights": insights,
                    "date": datetime.now().date().isoformat(),
                },
                "importance": 0.7,
            }
        )

    return {
        "topic": topic,
        "success": True,
        "insights_count": len(insights),
        "insights": insights,
        "materials": materials,
    }
