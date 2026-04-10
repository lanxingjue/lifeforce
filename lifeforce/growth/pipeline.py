"""成长输入收集与智能搜索触发。"""

from pathlib import Path
from typing import Any, Dict, List

from lifeforce.core.search_manager import SearchManager


def collect_inputs(
    memory: Any = None,
    vitals: Any = None,
    data_root: Path | None = None,
) -> Dict[str, List[Any]]:
    root = data_root or Path(".lifeforce")
    inputs: Dict[str, List[Any]] = {
        "creator_logs": _read_creator_logs(root),
        "system_logs": _read_system_logs(root),
        "materials": _read_materials(root),
        "self_outputs": _read_self_outputs(root),
        "env_changes": _read_env_changes(root),
    }
    search_manager = SearchManager(memory=memory, vitals=vitals, data_dir="data")

    for log in inputs.get("creator_logs", []):
        content = str(log.get("content", ""))
        if "学习" in content:
            result = search_manager.search("AI agent 最新进展", num_results=3)
            if result.get("success"):
                inputs["materials"].append({"type": "search_result", "insights": result.get("insights", [])})

    return inputs


def _read_creator_logs(root: Path) -> List[Dict[str, str]]:
    path = root / "creator_logs"
    if not path.exists():
        return []
    files = sorted(path.glob("*.md"), key=lambda p: p.stat().st_mtime, reverse=True)[:10]
    return [{"file": item.name, "content": item.read_text(encoding="utf-8", errors="ignore")} for item in files]


def _read_system_logs(root: Path) -> List[Dict[str, str]]:
    path = root / "system_logs"
    if not path.exists():
        return []
    files = sorted(path.glob("*.*"), key=lambda p: p.stat().st_mtime, reverse=True)[:20]
    return [{"file": item.name, "content": item.read_text(encoding="utf-8", errors="ignore")} for item in files]


def _read_materials(root: Path) -> List[Dict[str, str]]:
    path = root / "materials"
    if not path.exists():
        return []
    files = sorted(path.glob("*.*"), key=lambda p: p.stat().st_mtime, reverse=True)[:20]
    return [{"file": item.name, "content": item.read_text(encoding="utf-8", errors="ignore")} for item in files]


def _read_self_outputs(root: Path) -> List[Dict[str, str]]:
    path = root / "self_outputs"
    if not path.exists():
        return []
    files = sorted(path.glob("*.*"), key=lambda p: p.stat().st_mtime, reverse=True)[:20]
    return [{"file": item.name, "content": item.read_text(encoding="utf-8", errors="ignore")} for item in files]


def _read_env_changes(root: Path) -> List[Dict[str, str]]:
    path = root / "env_changes"
    if not path.exists():
        return []
    files = sorted(path.glob("*.*"), key=lambda p: p.stat().st_mtime, reverse=True)[:20]
    return [{"file": item.name, "content": item.read_text(encoding="utf-8", errors="ignore")} for item in files]
