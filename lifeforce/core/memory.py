"""Lifeforce 混合记忆系统（兼容 v1 + 增强 v2）。"""

from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
import json
import re
import sqlite3
import threading

from lifeforce.utils.logger import setup_logger

try:
    from mem0 import Memory as Mem0Memory  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    Mem0Memory = None


class MemorySystem:
    """
    兼容旧版 SQLite 接口，并新增 add/search/get_all 等记忆 2.0 能力。
    - v1 接口：write/read/stats
    - v2 接口：add/search/get_all/delete
    """

    def __init__(self, db_path: str = ".lifeforce/memory.db", config: Optional[Dict[str, Any]] = None) -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.logger = setup_logger("MemorySystem")
        self._lock = threading.RLock()
        self.conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._init_db()

        self.config = config or {}
        self.decay_enabled = self.config.get("decay_enabled", True)
        self.decay_half_life_days = int(self.config.get("decay_half_life_days", 30))
        self.mem0_mode = "primary"
        self.mem0_degraded_reason = ""
        self.mem0 = self._init_mem0(self.config)

    def _init_mem0(self, config: Dict[str, Any]) -> Any:
        if Mem0Memory is None:
            self.logger.info("mem0 未安装，使用本地混合检索降级模式")
            return None
        try:
            api_key = config.get("openai_api_key")
            if not api_key:
                api_key = config.get("api_key")
            if not api_key:
                api_key = config.get("llm_api_key")
            if not api_key:
                api_key = config.get("apiyi_api_key")

            base_url = (
                config.get("openai_base_url")
                or config.get("llm_base_url")
                or config.get("base_url")
                or "https://api.openai.com/v1"
            )
            mem0_config = {
                "vector_store": config.get(
                    "vector_store",
                    {"provider": "chroma", "config": {"path": "./data/chroma_db"}},
                ),
                "graph_store": config.get(
                    "graph_store",
                    {"provider": "kuzu", "config": {"db": "./data/kuzu_db"}},
                ),
                "llm": {
                    "provider": "openai",
                    "config": {
                        "api_key": api_key,
                        "openai_base_url": base_url,
                        "model": "gpt-4.1-nano",
                    },
                },
                "embedder": {
                    "provider": "openai",
                    "config": {
                        "api_key": api_key,
                        "openai_base_url": base_url,
                        "model": "text-embedding-3-small",
                    },
                },
            }
            mem0_instance = Mem0Memory.from_config(mem0_config)
            vector_provider = mem0_config["vector_store"].get("provider", "unknown")
            graph_provider = mem0_config["graph_store"].get("provider", "unknown")
            self.logger.info(
                "mem0 initialized with provider=%s+%s (mode=primary)",
                vector_provider,
                graph_provider,
            )
            return mem0_instance
        except Exception as exc:  # pragma: no cover - runtime fallback
            self.mem0_mode = "degraded"
            self.mem0_degraded_reason = str(exc)
            self.logger.warning("初始化 mem0 失败，降级到本地模式: %s", exc)
            return None

    def _init_db(self) -> None:
        with self._lock:
            cursor = self.conn.cursor()
            cursor.execute("PRAGMA journal_mode=WAL")
            cursor.execute("PRAGMA synchronous=NORMAL")
            cursor.execute("PRAGMA busy_timeout=5000")
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS memories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    type TEXT NOT NULL,
                    content TEXT NOT NULL,
                    importance REAL DEFAULT 0.5,
                    created_at TEXT NOT NULL,
                    last_accessed TEXT,
                    access_count INTEGER DEFAULT 0,
                    metadata TEXT
                )
                """
            )
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_type ON memories(type)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_created_at ON memories(created_at)")
            self.conn.commit()

    def memory_runtime_status(self) -> Dict[str, str]:
        mode = self.mem0_mode
        reason = self.mem0_degraded_reason
        if mode == "degraded" and re.search(r"lock|busy|could not set lock", reason, flags=re.IGNORECASE):
            mode = "degraded_lock_conflict"
        return {"mode": mode, "reason": reason}

    # -------- v1 compatibility --------
    def write(self, memory: Dict[str, Any]) -> int:
        with self._lock:
            cursor = self.conn.cursor()
            cursor.execute(
                """
                INSERT INTO memories (type, content, importance, created_at, metadata)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    memory.get("type", "unknown"),
                    json.dumps(memory, ensure_ascii=False),
                    float(memory.get("importance", 0.5)),
                    datetime.now().isoformat(),
                    json.dumps(memory.get("metadata", {}), ensure_ascii=False),
                ),
            )
            self.conn.commit()
            lastrowid = cursor.lastrowid
            return int(lastrowid) if lastrowid is not None else 0

    def read(self, memory_type: Optional[str] = None, limit: int = 10) -> List[Dict[str, Any]]:
        with self._lock:
            cursor = self.conn.cursor()
            if memory_type:
                cursor.execute(
                    """
                    SELECT id, type, content, importance, created_at, access_count
                    FROM memories
                    WHERE type = ?
                    ORDER BY created_at DESC
                    LIMIT ?
                    """,
                    (memory_type, limit),
                )
            else:
                cursor.execute(
                    """
                    SELECT id, type, content, importance, created_at, access_count
                    FROM memories
                    ORDER BY created_at DESC
                    LIMIT ?
                    """,
                    (limit,),
                )

            return [
                {
                    "id": row[0],
                    "type": row[1],
                    "content": json.loads(row[2]),
                    "importance": row[3],
                    "created_at": row[4],
                    "access_count": row[5],
                }
                for row in cursor.fetchall()
            ]

    # -------- v2 API --------
    def add(
        self,
        messages: List[Dict[str, str]],
        user_id: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> List[str]:
        metadata = metadata or {}
        metadata["user_id"] = user_id
        metadata["created_at"] = datetime.now().isoformat()

        ids: List[str] = []
        for fact in self._extract_facts(messages):
            memory_id = self.write(
                {
                    "type": "semantic_fact",
                    "content": {"memory": fact, "messages": messages},
                    "importance": self._estimate_importance(fact),
                    "metadata": metadata,
                }
            )
            ids.append(str(memory_id))

        if self.mem0 is not None:
            try:
                self.mem0.add(messages, user_id=user_id, metadata=metadata)
            except KeyError as exc:  # pragma: no cover
                self.mem0_mode = "degraded"
                self.mem0_degraded_reason = f"mem0 schema key missing: {exc}"
                self.logger.warning("mem0 add 出现实体字段缺失，降级到本地存储: %s", exc)
            except Exception as exc:  # pragma: no cover
                self.logger.warning("mem0 add 失败，继续使用本地存储: %s", exc)
        return ids

    def search(
        self,
        query: str,
        user_id: str,
        limit: int = 5,
        apply_decay: bool = True,
    ) -> List[Dict[str, Any]]:
        results: List[Dict[str, Any]] = []

        if self.mem0 is not None:
            try:
                mem0_results = self.mem0.search(query, user_id=user_id, limit=limit * 2)
                results.extend(self._normalize_mem0_results(mem0_results))
            except KeyError as exc:  # pragma: no cover
                self.mem0_mode = "degraded"
                self.mem0_degraded_reason = f"mem0 schema key missing: {exc}"
                self.logger.warning("mem0 search 出现实体字段缺失，降级本地检索: %s", exc)
            except Exception as exc:  # pragma: no cover
                self.logger.warning("mem0 search 失败，降级本地检索: %s", exc)

        results.extend(self._local_semantic_search(query, user_id=user_id, limit=limit * 4))
        deduped = self._dedupe_results(results)

        if apply_decay and self.decay_enabled:
            deduped = self._apply_decay(deduped)

        ranked = sorted(
            deduped,
            key=lambda m: (m.get("score", 0.0) * m.get("decay_factor", 1.0)),
            reverse=True,
        )[:limit]
        self._touch_memories(ranked)
        return ranked

    def get_all(self, user_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        with self._lock:
            cursor = self.conn.cursor()
            cursor.execute(
                """
                SELECT id, content, importance, created_at, metadata
                FROM memories
                WHERE metadata LIKE ?
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (f'%"user_id": "{user_id}"%', limit),
            )
            rows = cursor.fetchall()
            return [self._row_to_search_result(row, score=1.0) for row in rows]

    def delete(self, memory_id: str) -> None:
        with self._lock:
            cursor = self.conn.cursor()
            cursor.execute("DELETE FROM memories WHERE id = ?", (int(memory_id),))
            self.conn.commit()

    # -------- helpers --------
    def _extract_facts(self, messages: List[Dict[str, str]]) -> List[str]:
        user_text = " ".join(m.get("content", "") for m in messages if m.get("role") == "user").strip()
        if not user_text:
            return []
        facts: List[str] = []
        for marker in ["我叫", "我是", "我的项目叫", "项目叫", "我最喜欢", "我喜欢", "记住：", "记住"]:
            if marker in user_text:
                facts.append(user_text)
                break
        if not facts:
            facts.append(user_text)
        return facts

    def _estimate_importance(self, text: str) -> float:
        keywords = ["项目", "名字", "我叫", "我是", "喜欢", "偏好", "目标", "身份", "Lifeforce"]
        score = 0.4
        for kw in keywords:
            if kw in text:
                score += 0.08
        return max(0.3, min(score, 1.0))

    def _tokenize(self, text: str) -> List[str]:
        separators = ["，", "。", "！", "？", ",", ".", "!", "?", "：", ":", "\n", "\t"]
        for sep in separators:
            text = text.replace(sep, " ")
        tokens = [token.strip().lower() for token in text.split(" ") if token.strip()]
        compact = "".join(tokens)
        if compact:
            bigrams = [compact[i : i + 2] for i in range(max(len(compact) - 1, 0))]
            tokens.extend(bigrams)
        return tokens

    def _local_semantic_search(self, query: str, user_id: str, limit: int) -> List[Dict[str, Any]]:
        query_tokens = set(self._tokenize(query))
        if not query_tokens:
            return []

        with self._lock:
            cursor = self.conn.cursor()
            cursor.execute(
                """
                SELECT id, content, importance, created_at, metadata, access_count
                FROM memories
                WHERE metadata LIKE ?
                ORDER BY created_at DESC
                LIMIT 500
                """,
                (f'%"user_id": "{user_id}"%',),
            )
            rows = cursor.fetchall()
        scored: List[Dict[str, Any]] = []
        for row in rows:
            content_dict = json.loads(row["content"])
            text = content_dict.get("memory") or content_dict.get("content") or json.dumps(content_dict, ensure_ascii=False)
            text_str = text if isinstance(text, str) else json.dumps(text, ensure_ascii=False)
            memory_tokens = set(self._tokenize(text_str))
            if not memory_tokens:
                continue
            overlap = len(query_tokens & memory_tokens)
            if overlap == 0:
                continue
            union = len(query_tokens | memory_tokens)
            lexical_score = overlap / max(union, 1)
            importance = float(row["importance"] or 0.5)
            score = lexical_score * 0.75 + importance * 0.25
            scored.append(self._row_to_search_result(row, score=score))
        return sorted(scored, key=lambda x: x.get("score", 0.0), reverse=True)[:limit]

    def _row_to_search_result(self, row: sqlite3.Row, score: float) -> Dict[str, Any]:
        content_dict = json.loads(row["content"])
        metadata = json.loads(row["metadata"] or "{}")
        memory_text = content_dict.get("memory") or content_dict.get("content") or json.dumps(content_dict, ensure_ascii=False)
        if not isinstance(memory_text, str):
            memory_text = json.dumps(memory_text, ensure_ascii=False)
        return {
            "id": str(row["id"]),
            "memory": memory_text,
            "content": memory_text,
            "score": float(score),
            "importance": float(row["importance"] or 0.5),
            "created_at": row["created_at"],
            "access_count": int(row["access_count"]) if "access_count" in row.keys() and row["access_count"] is not None else 0,
            "metadata": metadata,
            "source": "local",
        }

    def _normalize_mem0_results(self, mem0_results: Any) -> List[Dict[str, Any]]:
        normalized: List[Dict[str, Any]] = []
        if not isinstance(mem0_results, list):
            return normalized
        for item in mem0_results:
            if isinstance(item, dict):
                try:
                    normalized.append(
                        {
                            "id": str(item.get("id", "")),
                            "entity_type": str(item.get("entity_type", "Unknown")),
                            "memory": item.get("memory", item.get("content", "")),
                            "content": item.get("content", item.get("memory", "")),
                            "score": float(item.get("score", 0.6)),
                            "metadata": item.get("metadata", {}),
                            "source": "mem0",
                        }
                    )
                except Exception as exc:
                    self.logger.warning("跳过异常 mem0 结果项: %s | item=%s", exc, str(item)[:200])
        return normalized

    def _dedupe_results(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        seen: Dict[str, Dict[str, Any]] = {}
        for item in results:
            key = (item.get("memory") or "").strip().lower()
            if not key:
                continue
            if key not in seen or item.get("score", 0) > seen[key].get("score", 0):
                seen[key] = item
        return list(seen.values())

    def _apply_decay(self, memories: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        now = datetime.now()
        for memory in memories:
            created_at = (
                memory.get("metadata", {}).get("last_accessed_at")
                or memory.get("metadata", {}).get("created_at")
                or memory.get("created_at")
            )
            if not created_at:
                memory["decay_factor"] = 1.0
                continue
            try:
                dt = datetime.fromisoformat(created_at)
            except ValueError:
                memory["decay_factor"] = 1.0
                continue
            days_since = max((now - dt).days, 0)
            memory["decay_factor"] = 0.5 ** (days_since / max(self.decay_half_life_days, 1))
        return memories

    def _touch_memories(self, memories: List[Dict[str, Any]]) -> None:
        ids = [m.get("id") for m in memories if m.get("source") == "local" and m.get("id")]
        if not ids:
            return
        with self._lock:
            cursor = self.conn.cursor()
            now = datetime.now().isoformat()
            for memory_id in ids:
                parsed_id = int(memory_id) if memory_id is not None else 0
                cursor.execute(
                    """
                    UPDATE memories
                    SET last_accessed = ?, access_count = access_count + 1
                    WHERE id = ?
                    """,
                    (now, parsed_id),
                )
            self.conn.commit()

    def stats(self) -> Dict[str, Any]:
        with self._lock:
            cursor = self.conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM memories")
            total_count = cursor.fetchone()[0]
            cursor.execute(
                """
                SELECT type, COUNT(*) as count
                FROM memories
                GROUP BY type
                ORDER BY count DESC
                """
            )
            type_counts = {row[0]: row[1] for row in cursor.fetchall()}
            return {"total_count": total_count, "type_counts": type_counts}

    def close(self) -> None:
        self.conn.close()
