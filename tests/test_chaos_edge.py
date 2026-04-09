from lifeforce.genome.chaos_edge import ChaosEdgeConfig, ChaosEdgeController, adjust_temperature, get_chaos_stats, inject_randomness


def test_should_explore_respects_temperature() -> None:
    controller = ChaosEdgeController(ChaosEdgeConfig(temperature="high"))
    results = [controller.should_explore() for _ in range(300)]
    ratio = sum(results) / len(results)
    assert ratio > 0.15


def test_inject_randomness_returns_candidates() -> None:
    ordered = inject_randomness(["shell_exec", "llm_call", "memory_write"], top_k=2)
    assert len(ordered) == 3
    assert set(ordered) == {"shell_exec", "llm_call", "memory_write"}


def test_adjust_temperature_and_stats() -> None:
    temperature = adjust_temperature("system stuck in 局部最优")
    stats = get_chaos_stats()
    assert temperature in {"low", "medium", "high"}
    assert stats["current_temperature"] == temperature
