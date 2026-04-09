from pathlib import Path
import os

from lifeforce.core.search_manager import SearchManager
from lifeforce.core.memory import MemorySystem
from lifeforce.growth.learning import learning_pipeline
from lifeforce.memory.world_model import WorldModel


def test_search_manager_classify_intent() -> None:
    manager = SearchManager()
    assert manager.classify_intent("什么是自组织") == "fact"
    assert manager.classify_intent("最新 AI 趋势") == "trend"
    assert manager.classify_intent("学习复杂系统") == "learning"


def test_search_manager_extract_and_save(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.chdir(tmp_path)
    (tmp_path / "data").mkdir(parents=True, exist_ok=True)
    memory = MemorySystem(str(tmp_path / "search_mem.db"), config={"data_dir": str(tmp_path)})

    class _Tool:
        def search(self, query: str, num_results: int = 5):
            return [
                {"title": "A", "link": "https://arxiv.org/abs/123", "snippet": "tutorial introduction"},
                {"title": "B", "link": "https://example.com", "snippet": "recent trend"},
            ]

    monkeypatch.setattr("lifeforce.core.search_manager.GoogleSearchTool", _Tool)
    world_model = WorldModel()
    manager = SearchManager(memory=memory, vitals=None, world_model=world_model)
    result = manager.search("学习 agent 架构", intent="learning", num_results=2)
    assert result["success"] is True
    assert result["insights"]
    manager.save_insights_to_memory(result["insights"], "学习 agent 架构")
    saved = memory.read(memory_type="search_insight", limit=5)
    assert saved
    assert os.path.exists(tmp_path / "data" / "search_stats.json")
    assert world_model.model["facts"]
    memory.close()


def test_world_model_update_from_insights(tmp_path: Path) -> None:
    model = WorldModel(data_dir=str(tmp_path / "data"))
    model.update_from_insights(
        [
            {"type": "fact", "summary": "AI agents are moving to multi-agent", "source": "https://a"},
            {"type": "trend", "summary": "real-time retrieval is becoming standard", "source": "https://b"},
        ]
    )
    assert len(model.model["facts"]) >= 1
    assert len(model.model["trends"]) >= 1


def test_learning_pipeline_updates_world_and_memory(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.chdir(tmp_path)
    (tmp_path / "data").mkdir(parents=True, exist_ok=True)
    memory = MemorySystem(str(tmp_path / "learn_mem.db"), config={"data_dir": str(tmp_path)})

    class _Tool:
        def search(self, query: str, num_results: int = 5):
            return [{"title": "A", "link": "https://arxiv.org/abs/xyz", "snippet": "introduction guide"}]

    monkeypatch.setattr("lifeforce.core.search_manager.GoogleSearchTool", _Tool)
    result = learning_pipeline("artificial life", memory=memory, vitals=None, data_root=tmp_path)
    assert result["success"] is True
    assert result["insights_count"] >= 1
    assert result["materials"][0]["url"] != ""
    assert memory.read(memory_type="learning", limit=5)
    model = WorldModel()
    assert len(model.model["facts"]) >= 1
    memory.close()
