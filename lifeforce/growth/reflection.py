"""深度反思：引用世界模型与搜索统计。"""

from datetime import datetime
from pathlib import Path
from typing import Any, Dict

from lifeforce.core.search_manager import SearchManager
from lifeforce.memory.world_model import WorldModel


def reflect_deep(
    memory: Any = None,
    vitals: Any = None,
    self_model: Any = None,
    data_root: Path | None = None,
) -> Dict[str, Any]:
    _ = data_root
    world_model = WorldModel()
    search_manager = SearchManager(memory=memory, vitals=vitals, data_dir="data")

    reflection = "今日反思:\n\n"
    reflection += "【世界模型更新】\n"
    reflection += f"最近学到的事实: {len(world_model.model['facts'])} 条\n"
    reflection += f"最近观察到的趋势: {len(world_model.model['trends'])} 条\n"
    reflection += "\n【搜索效率反思】\n"
    reflection += f"今日搜索次数: {search_manager.get_search_stats().get('total_searches', 0)}\n"
    reflection += "\n【策略】\n"
    reflection += "明日策略: 保持有限高质量搜索，优先学习与数字生命系统相关材料。\n"

    if self_model is not None:
        self_model.upsert_limitation("搜索洞察到世界模型的映射仍需持续校准")
        self_model.upsert_forming_capability("世界模型稳定更新")
        self_model.set_next_strategy(["减少低相关搜索，提升洞察质量"])
        self_model.increment_evolution_count()
        self_model.set_last_reflection(datetime.now().date().isoformat())

    if memory is not None and hasattr(memory, "write"):
        memory.write({"type": "reflection_report", "content": {"text": reflection}, "importance": 0.8})

    return {
        "text": reflection,
        "world_model_summary": world_model.get_summary(),
        "search_stats": search_manager.get_search_stats(),
        "limitation": "搜索洞察到世界模型的映射仍需持续校准",
        "strategy": "减少低相关搜索，提升洞察质量",
        "missing_capability": "实时趋势检索",
        "learning_topic": "artificial life",
    }
