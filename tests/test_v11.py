from pathlib import Path

from lifeforce.genome import load_constitution, load_genome
from lifeforce.heartbeat import CoreHeartbeat
from lifeforce.memory.emergence import EmergenceDetector
from lifeforce.memory.self_model import SelfModelStore


class DummyBudget:
    def get_usage(self):
        return {"hourly": {"used": 10, "remaining": 90}}


class DummyMemory:
    def __init__(self) -> None:
        self.records = []

    def read(self, limit=1):
        return self.records[-limit:]

    def write(self, payload):
        self.records.append(payload)
        return len(self.records)


def test_genome_and_constitution_load() -> None:
    genome = load_genome()
    constitution = load_constitution()
    assert genome.version == "1.1"
    assert "authenticity" in genome.value_genes
    assert constitution.status == "Active"


def test_self_model_store_reflect_description(tmp_path: Path) -> None:
    store = SelfModelStore(tmp_path / "self_model")
    description = store.get_self_description()
    assert "Lifeforce" in description
    store.update_capability("coding", 0.9)
    assert "coding" in store.get_self_description()


def test_emergence_detector_detect(tmp_path: Path) -> None:
    genome = load_genome()
    detector = EmergenceDetector(tmp_path / "emergence", genome)
    event = detector.detect(
        agents_involved=["Orchestrator", "Executor"],
        expected_outcome="完成任务A",
        actual_outcome="完成任务A，并自动生成测试、优化架构、补全文档、执行回归验证与性能评估",
        context={"success": True, "is_novel": True},
    )
    assert event is not None
    assert event.value_score >= 0.7


def test_heartbeat_persist() -> None:
    memory = DummyMemory()
    heartbeat = CoreHeartbeat(memory, DummyBudget())
    heartbeat.start()
    for _ in range(60):
        heartbeat.beat()
    assert any(record.get("type") == "heartbeat" for record in memory.records)
