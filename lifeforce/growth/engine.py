"""Lifeforce 持续成长引擎（最小影响版）。"""

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List
import json
import subprocess

from lifeforce.agents.thinker import ThinkerAgent
from lifeforce.core.memory import MemorySystem
from lifeforce.genome import load_genome
from lifeforce.growth.learning import learning_pipeline
from lifeforce.growth.pipeline import collect_inputs as collect_inputs_pipeline
from lifeforce.growth.reflection import reflect_deep as reflect_deep_pipeline
from lifeforce.memory.emergence import EmergenceDetector
from lifeforce.memory.self_model import SelfModelStore
from lifeforce.utils.logger import setup_logger


@dataclass
class GrowthInputs:
    creator_logs: List[str]
    system_logs: List[str]
    materials: List[str]
    self_outputs: List[str]
    env_changes: List[str]

    def to_dict(self) -> Dict[str, List[str]]:
        return {
            "creator_logs": self.creator_logs,
            "system_logs": self.system_logs,
            "materials": self.materials,
            "self_outputs": self.self_outputs,
            "env_changes": self.env_changes,
        }


class SkillLifecycleManager:
    """技能搜索与安装管理器。"""

    _SKILL_CATALOG: List[Dict[str, Any]] = [
        {"id": "skill:web-search", "name": "web-search", "intent": ["实时信息", "搜索", "检索"], "risk": "low"},
        {"id": "skill:image-gen", "name": "image-generation", "intent": ["图片生成", "图像", "视觉"], "risk": "medium"},
        {"id": "skill:data-analysis", "name": "data-analysis", "intent": ["数据分析", "统计", "表格"], "risk": "low"},
    ]

    def __init__(self, data_root: Path, self_model: SelfModelStore) -> None:
        self.logger = setup_logger("SkillLifecycleManager")
        self.data_root = data_root
        self.self_model = self_model
        self.registry_file = self.data_root / "skills" / "installed_skills.json"
        self.registry_file.parent.mkdir(parents=True, exist_ok=True)

    def search(self, capability: str, limit: int = 3) -> List[Dict[str, Any]]:
        tokens = capability.lower()
        matched = [s for s in self._SKILL_CATALOG if any(keyword in tokens for keyword in s["intent"])]
        if not matched:
            matched = self._SKILL_CATALOG[:]
        return matched[:limit]

    def install(self, skill_id: str) -> Dict[str, Any]:
        skill = next((s for s in self._SKILL_CATALOG if s["id"] == skill_id), None)
        if skill is None:
            raise ValueError(f"未知 skill_id: {skill_id}")
        installed = self._read_registry()
        if not any(item.get("id") == skill_id for item in installed):
            installed.append(
                {
                    "id": skill_id,
                    "name": skill["name"],
                    "installed_at": datetime.now().isoformat(),
                    "status": "active",
                }
            )
            self.registry_file.write_text(json.dumps(installed, ensure_ascii=False, indent=2), encoding="utf-8")
        self.self_model.add_current_capability_label(skill["name"])
        self.self_model.record_evolution(
            {"type": "skill_install", "description": f"主动安装新能力: {skill['name']}", "skill_id": skill_id}
        )
        return skill

    def _read_registry(self) -> List[Dict[str, Any]]:
        if not self.registry_file.exists():
            return []
        raw = json.loads(self.registry_file.read_text(encoding="utf-8"))
        if isinstance(raw, list):
            return [item for item in raw if isinstance(item, dict)]
        return []


class LearningPipeline:
    """材料学习流水线。"""

    def __init__(self, data_root: Path, memory: MemorySystem, thinker: ThinkerAgent) -> None:
        self.logger = setup_logger("LearningPipeline")
        self.data_root = data_root
        self.memory = memory
        self.thinker = thinker

    def search_materials(self, topic: str, limit: int = 3) -> List[Dict[str, str]]:
        manual_file = self.data_root / "materials" / "manual_urls.txt"
        urls: List[str] = []
        if manual_file.exists():
            urls.extend([line.strip() for line in manual_file.read_text(encoding="utf-8").splitlines() if line.strip()])
        if not urls:
            urls = [
                f"https://example.com/{topic}/intro",
                f"https://example.com/{topic}/practice",
                f"https://example.com/{topic}/systems",
            ]
        return [{"url": item, "title": f"{topic} 学习材料"} for item in urls[:limit]]

    def learn_topic(self, topic: str, limit: int = 3) -> Dict[str, Any]:
        result = learning_pipeline(topic=topic, memory=self.memory, vitals=None, data_root=self.data_root)
        materials = list(result.get("materials", []))
        insights = list(result.get("insights", []))
        if limit > 0:
            materials = materials[:limit]
            insights = insights[: max(limit, len(insights))]
        return {
            "topic": result.get("topic", topic),
            "success": result.get("success", True),
            "insights_count": result.get("insights_count", len(insights)),
            "materials": materials,
            "insights": insights,
        }


class GrowthEngine:
    """输入-反思-进化的持续成长闭环。"""

    def __init__(self, data_root: Path, memory: MemorySystem, thinker: ThinkerAgent, self_model: SelfModelStore) -> None:
        self.logger = setup_logger("GrowthEngine")
        self.data_root = data_root
        self.memory = memory
        self.thinker = thinker
        self.self_model = self_model
        self.skill_manager = SkillLifecycleManager(data_root, self_model)
        self.learning = LearningPipeline(data_root, memory, thinker)
        self.emergence = EmergenceDetector(data_root / "emergence", load_genome())
        self._ensure_dirs()

    def run_growth_cycle(self) -> Dict[str, Any]:
        inputs = self.collect_inputs()
        reflection = self.reflect_deep(inputs)
        gap = reflection.get("missing_capability", "实时信息搜索")
        skills = self.skill_manager.search(gap, limit=3)
        installed = self.skill_manager.install(skills[0]["id"]) if skills else None
        learning_topic = reflection.get("learning_topic", "混沌边缘")
        learned = self.learning.learn_topic(learning_topic, limit=1)
        return {
            "inputs": inputs.to_dict(),
            "reflection": reflection,
            "installed_skill": installed,
            "learning": learned,
        }

    def collect_inputs(self) -> GrowthInputs:
        collected = collect_inputs_pipeline(memory=self.memory, vitals=None, data_root=self.data_root)
        creator_logs = [str(item.get("content", "")) for item in collected.get("creator_logs", [])]
        system_logs = [str(item.get("content", "")) for item in collected.get("system_logs", [])]
        materials = [
            str(item) if not isinstance(item, dict) else str(item.get("insights", item.get("content", "")))
            for item in collected.get("materials", [])
        ]
        self_outputs = [str(item.get("content", "")) for item in collected.get("self_outputs", [])]
        env_changes = [str(item.get("content", "")) for item in collected.get("env_changes", [])]
        return GrowthInputs(
            creator_logs=creator_logs,
            system_logs=system_logs,
            materials=materials,
            self_outputs=self_outputs,
            env_changes=env_changes,
        )

    def reflect_deep(self, inputs: GrowthInputs) -> Dict[str, Any]:
        _ = inputs
        result = reflect_deep_pipeline(memory=self.memory, vitals=None, self_model=self.self_model, data_root=self.data_root)
        emergence = self.emergence.detect(
            agents_involved=["Orchestrator", "Thinker", "SelfModeler"],
            expected_outcome="稳定身份一致性回答",
            actual_outcome="在多类问题下保持身份锚点并可解释局限",
            context={"success": True, "is_novel": True},
        )
        result["emergence"] = emergence.to_dict() if emergence else None
        return result

    def _update_self_model_after_reflection(self, limitation: str, strategy: str) -> None:
        self.self_model.upsert_limitation(limitation)
        self.self_model.upsert_forming_capability("长期记忆代谢稳定化")
        self.self_model.set_next_strategy([strategy])
        self.self_model.increment_evolution_count()
        self.self_model.set_last_reflection(datetime.now().date().isoformat())

    def _read_text_pool(self, path: Path, pattern: str, limit: int) -> List[str]:
        if not path.exists():
            return []
        files = sorted(path.glob(pattern), key=lambda f: f.stat().st_mtime, reverse=True)[:limit]
        return [file.read_text(encoding="utf-8", errors="ignore")[:800] for file in files if file.is_file()]

    def _read_system_logs(self) -> List[str]:
        result: List[str] = []
        result.extend(self._read_text_pool(self.data_root / "system_logs", "*.*", limit=8))
        log_file = self.data_root / "logs" / "error.log"
        if log_file.exists():
            result.append(log_file.read_text(encoding="utf-8", errors="ignore")[-1000:])
        return result

    def _read_env_changes(self) -> List[str]:
        changes: List[str] = []
        changes.extend(self._read_text_pool(self.data_root / "env_changes", "*.*", limit=6))
        try:
            diff = subprocess.check_output(
                ["git", "diff", "--name-only"],
                cwd=self.data_root.parent,
                text=True,
                encoding="utf-8",
                errors="ignore",
                timeout=5,
            )
            if diff.strip():
                changes.append(diff.strip())
            log = subprocess.check_output(
                ["git", "log", "-n", "3", "--pretty=%s"],
                cwd=self.data_root.parent,
                text=True,
                encoding="utf-8",
                errors="ignore",
                timeout=5,
            )
            if log.strip():
                changes.append(log.strip())
        except Exception:
            pass
        return changes

    def _ensure_dirs(self) -> None:
        for sub in ["creator_logs", "system_logs", "materials", "self_outputs", "env_changes", "skills", "logs"]:
            (self.data_root / sub).mkdir(parents=True, exist_ok=True)
