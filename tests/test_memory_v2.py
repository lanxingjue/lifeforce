from pathlib import Path

from lifeforce.core.memory import MemorySystem


def test_memory_v2_add_and_search() -> None:
    db_path = Path(".lifeforce/test_memory_v2.db")
    db_path.parent.mkdir(exist_ok=True)
    memory = MemorySystem(
        str(db_path),
        config={
            "decay_enabled": True,
            "decay_half_life_days": 30,
            "vector_store": {"provider": "chroma", "config": {"path": "./test_chroma"}},
            "graph_store": {"provider": "kuzu", "config": {"db": "./test_kuzu_db"}},
        },
    )
    try:
        memory.add(
            messages=[
                {"role": "user", "content": "我叫 Wells"},
                {"role": "assistant", "content": "你好 Wells"},
            ],
            user_id="wells",
        )
        memory.add(
            messages=[
                {"role": "user", "content": "我的项目叫 Lifeforce，它是一个数字生命"},
                {"role": "assistant", "content": "记住了"},
            ],
            user_id="wells",
        )

        results = memory.search("我的项目叫什么？", user_id="wells", limit=3)
        assert results, "应至少检索到一条记忆"
        assert any("Lifeforce" in (r.get("memory", "") or "") for r in results)
        assert all("decay_factor" in r for r in results)
    finally:
        memory.close()
        db_path.unlink(missing_ok=True)
