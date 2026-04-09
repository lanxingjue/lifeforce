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
        materials = self.search_materials(topic, limit=limit)
        insights: List[str] = []
        for item in materials:
            content = f"材料主题: {topic}; 来源: {item['url']}; 核心: 复杂系统中的反馈、代谢、涌现。"
            guided = self.thinker.think_with_tool(
                problem=f"提取{topic}的关键洞察",
                tool_name="first_principles",
                context={"source": item["url"]},
            )
            insight = f"{content}\n{guided}"
            insights.append(insight)
            self.memory.write(
                {
                    "type": "learning",
                    "content": {
                        "topic": topic,
                        "source": item["url"],
                        "insight": insight,
                        "date": datetime.now().date().isoformat(),
                    },
                    "importance": 0.65,
                }
            )
        return {"topic": topic, "materials": materials, "insights": insights}


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
        creator_logs = self._read_text_pool(self.data_root / "creator_logs", "*.md", limit=5)
        system_logs = self._read_system_logs()
        materials = self._read_text_pool(self.data_root / "materials", "*.*", limit=3)
        self_outputs = self._read_text_pool(self.data_root / "self_outputs", "*.*", limit=6)
        env_changes = self._read_env_changes()
        return GrowthInputs(
            creator_logs=creator_logs,
            system_logs=system_logs,
            materials=materials,
            self_outputs=self_outputs,
            env_changes=env_changes,
        )

    def reflect_deep(self, inputs: GrowthInputs) -> Dict[str, Any]:
        events = (inputs.creator_logs + inputs.system_logs + inputs.materials + inputs.self_outputs + inputs.env_changes)[:20]
        top3 = events[:3] if events else ["无显著事件", "无显著事件", "无显著事件"]
        limitation = "自我模型尚未在所有回答路径稳定生效"
        strategy = "将状态查询和价值观约束覆盖到更多普通对话路径"
        reflection_text = (
            "今日反思:\n"
            f"1) 重要事件: {top3}\n"
            "2) 重复模式: 用户持续追问身份一致性与状态透明度\n"
            "3) 结构性失败: 个别路径会退化为通用助手语气\n"
            "4) 最像 Lifeforce 的行为: 以宪法约束拒绝违背价值观请求\n"
            "5) 最不像 Lifeforce 的行为: 在上下文不足时给出空泛回答\n"
            f"6) 当前局限: {limitation}\n"
            "7) 成功模式: 身份 responder + 状态 responder 的协同\n"
            f"8) 明日策略: {strategy}\n"
        )
        self._update_self_model_after_reflection(limitation=limitation, strategy=strategy)
        self.memory.write({"type": "reflection_report", "content": {"text": reflection_text}, "importance": 0.8})
        emergence = self.emergence.detect(
            agents_involved=["Orchestrator", "Thinker", "SelfModeler"],
            expected_outcome="稳定身份一致性回答",
            actual_outcome="在多类问题下保持身份锚点并可解释局限",
            context={"success": True, "is_novel": True},
        )
        return {
            "text": reflection_text,
            "limitation": limitation,
            "strategy": strategy,
            "emergence": emergence.to_dict() if emergence else None,
            "missing_capability": "实时信息搜索",
            "learning_topic": "混沌边缘",
        }

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
