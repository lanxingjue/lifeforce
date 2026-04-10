from pathlib import Path

from lifeforce.agents.market_observer import MarketObserver
from lifeforce.core.budget import BudgetGuard
from lifeforce.core.memory import MemorySystem
from lifeforce.memory.self_model import SelfModelStore
from lifeforce.memory.world_model import WorldModel
from lifeforce.trading.daemon import run_hourly_reflection, run_trade_cycle
from lifeforce.trading.simulator import TradingSimulator
from lifeforce.trading.strategies.grid_strategy import GridStrategy
from lifeforce.trading.strategies.trend_strategy import TrendStrategy


class FakeExchange:
    def fetch_ticker(self, symbol: str):
        prices = {"BTC/USDT": 70000.0, "ETH/USDT": 3500.0}
        return {"last": prices.get(symbol, 0.0)}

    def fetch_ohlcv(self, symbol: str, timeframe: str = "1h", limit: int = 100):
        return [[1, 2, 3, 4, 5, 6] for _ in range(limit)]


def test_run_trade_cycle_and_reflection(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    memory = MemorySystem(str(tmp_path / "daemon.db"), config={"data_dir": str(tmp_path)})
    observer = MarketObserver(memory=memory, budget_guard=BudgetGuard(), exchange=FakeExchange())
    world_model = WorldModel()
    simulator = TradingSimulator(memory=memory, world_model=world_model, state_path=Path(".lifeforce/trading/state.json"))
    result = run_trade_cycle(
        observer=observer,
        simulator=simulator,
        world_model=world_model,
        trend_strategy=TrendStrategy(fast_window=3, slow_window=5),
        grid_strategy=GridStrategy(symbol="BTC/USDT", grid_size=5, lower_price=60000, upper_price=80000),
    )
    assert "final_signal" in result
    self_model = SelfModelStore(tmp_path / "self_model")
    reflection = run_hourly_reflection(memory=memory, self_model=self_model)
    assert "交易反思" in reflection["text"]
    memory.close()
