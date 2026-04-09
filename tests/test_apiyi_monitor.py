from lifeforce.core.apiyi_monitor import ApiyiMonitor


def test_apiyi_monitor_usage_summary(monkeypatch) -> None:
    class _Resp:
        def raise_for_status(self) -> None:
            return None

        def json(self):
            return {
                "data": [
                    {"quota": 10, "prompt_tokens": 100, "completion_tokens": 20, "model_name": "gpt-4.1-nano"},
                    {"quota": 5, "prompt_tokens": 50, "completion_tokens": 10, "model_name": "gpt-4.1-nano"},
                    {"quota": 8, "prompt_tokens": 80, "completion_tokens": 16, "model_name": "text-embedding-3-small"},
                ]
            }

    monkeypatch.setenv("APIYI_BALANCE_USD", "30")
    monkeypatch.setenv("APIYI_USD_PER_QUOTA", "0.01")
    monkeypatch.setattr("lifeforce.core.apiyi_monitor.httpx.get", lambda *args, **kwargs: _Resp())
    monitor = ApiyiMonitor("test-key")
    usage = monitor.summarize_usage(page_size=10)
    assert usage["quota_used_recent"] == 23
    assert usage["prompt_tokens_recent"] == 230
    assert usage["completion_tokens_recent"] == 46
    assert usage["estimated_used_usd_recent"] == 0.23
    assert usage["estimated_remaining_usd"] == 29.77


def test_apiyi_monitor_model_suggestion_fallback(monkeypatch) -> None:
    monkeypatch.setenv("APIYI_MODEL_CANDIDATES", "MiniMax-M2.7,gpt-4.1-nano")

    class _Resp:
        def raise_for_status(self) -> None:
            return None

        @property
        def text(self) -> str:
            return "<html>model list unavailable</html>"

    monkeypatch.setattr("lifeforce.core.apiyi_monitor.httpx.get", lambda *args, **kwargs: _Resp())
    monitor = ApiyiMonitor("test-key")
    models = monitor.suggest_models()
    assert "MiniMax-M2.7" in models
