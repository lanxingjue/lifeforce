"""APIYI 用量与模型监控。"""

from collections import Counter
import os
import re
from typing import Any, Dict, List

import httpx

from lifeforce.utils.logger import setup_logger


class ApiyiMonitor:
    """读取 APIYI 日志并生成可读监控摘要。"""

    def __init__(self, api_key: str) -> None:
        self.api_key = api_key
        self.logger = setup_logger("ApiyiMonitor")
        self.log_url = "https://api.apiyi.com/public/log/self/search"
        self.pricing_url = "https://api.apiyi.com/account/pricing"

    def summarize_usage(self, page_size: int = 10) -> Dict[str, Any]:
        logs = self._fetch_logs(page_size=page_size)
        items = logs.get("data", []) if isinstance(logs, dict) else []
        quota_used = 0
        prompt_tokens = 0
        completion_tokens = 0
        model_counter: Counter[str] = Counter()

        for item in items:
            if not isinstance(item, dict):
                continue
            quota_used += int(item.get("quota", 0) or 0)
            prompt_tokens += int(item.get("prompt_tokens", 0) or 0)
            completion_tokens += int(item.get("completion_tokens", 0) or 0)
            model_name = str(item.get("model_name", "unknown"))
            model_counter[model_name] += 1

        usd_per_quota = float(os.getenv("APIYI_USD_PER_QUOTA", "0.001"))
        estimated_used_usd = quota_used * usd_per_quota
        balance_usd = float(os.getenv("APIYI_BALANCE_USD", "30"))
        remaining_usd = max(balance_usd - estimated_used_usd, 0.0)

        return {
            "quota_used_recent": quota_used,
            "prompt_tokens_recent": prompt_tokens,
            "completion_tokens_recent": completion_tokens,
            "estimated_used_usd_recent": round(estimated_used_usd, 4),
            "estimated_remaining_usd": round(remaining_usd, 4),
            "model_usage_recent": dict(model_counter),
        }

    def suggest_models(self) -> List[str]:
        try:
            response = httpx.get(self.pricing_url, params={"key": self.api_key}, timeout=20.0)
            response.raise_for_status()
            text = response.text
            # pricing 页面是 HTML，解析常见模型名。
            pattern = r"(GPT-[A-Za-z0-9\.\-]+|Claude\s*\d+(\.\d+)?|Gemini-[A-Za-z0-9\.\-]+|Grok-[A-Za-z0-9\.\-]+|Sora\s*2|Nano Banana Pro)"
            matched = re.findall(pattern, text, flags=re.IGNORECASE)
            models: List[str] = []
            for item in matched:
                value = item[0] if isinstance(item, tuple) else item
                cleaned = re.sub(r"\s+", " ", str(value)).strip()
                if cleaned and cleaned not in models:
                    models.append(cleaned)
            configured = os.getenv("APIYI_MODEL_CANDIDATES", "")
            if configured:
                for model in [m.strip() for m in configured.split(",") if m.strip()]:
                    if model not in models:
                        models.append(model)
            return models[:12]
        except Exception as exc:
            self.logger.warning("获取模型列表失败，使用配置兜底: %s", exc)
            configured = os.getenv("APIYI_MODEL_CANDIDATES", "")
            if configured:
                return [m.strip() for m in configured.split(",") if m.strip()]
            return ["MiniMax-M2.7", "gpt-4.1-nano", "gpt-4.1", "claude-3-5-sonnet"]

    def _fetch_logs(self, page_size: int) -> Dict[str, Any]:
        try:
            response = httpx.get(
                self.log_url,
                params={"key": self.api_key, "p": 0, "pageSize": page_size},
                timeout=20.0,
            )
            response.raise_for_status()
            data = response.json()
            if isinstance(data, dict):
                return data
            return {}
        except Exception as exc:
            self.logger.warning("拉取 APIYI 日志失败: %s", exc)
            return {}
