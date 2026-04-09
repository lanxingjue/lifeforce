from pathlib import Path

from lifeforce.core.memory import MemorySystem


def test_memory_stats() -> None:
    db_path = Path(".lifeforce/test_memory_stats.db")
    db_path.parent.mkdir(exist_ok=True)
    memory = MemorySystem(str(db_path))
    try:
        memory.write({"type": "unit_test", "content": {"x": 1}})
        stats = memory.stats()
        assert stats["total_count"] >= 1
        assert "unit_test" in stats["type_counts"]
    finally:
        memory.close()
        db_path.unlink(missing_ok=True)

