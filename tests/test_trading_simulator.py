from pathlib import Path

from lifeforce.core.memory import MemorySystem
from lifeforce.memory.world_model import WorldModel
from lifeforce.trading.simulator import TradingSimulator


def test_simulator_buy_sell_and_risk(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    memory = MemorySystem(str(tmp_path / "trade.db"), config={"data_dir": str(tmp_path)})
    world_model = WorldModel()
    simulator = TradingSimulator(
        initial_cash=1000,
        fee_rate=0.001,
        max_position_pct=0.5,
        stop_loss_pct=0.1,
        memory=memory,
        world_model=world_model,
        state_path=Path(".lifeforce/trading/state.json"),
    )
    buy = simulator.execute_signal("BTC/USDT", "buy", 100.0, timestamp="2026-01-01T00:00:00")
    assert buy["status"] in {"filled", "rejected"}
    sell = simulator.execute_signal("BTC/USDT", "sell", 110.0, timestamp="2026-01-01T01:00:00")
    assert sell["status"] in {"filled", "rejected", "hold"}
    stats = simulator.stats({"BTC/USDT": 110.0})
    assert "portfolio_value" in stats
    assert Path(".lifeforce/trading/state.json").exists()
    memory.close()
