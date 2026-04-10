from datetime import datetime
from typing import Any, Dict, List

from lifeforce.agents.market_observer import MarketObserver
from lifeforce.core.memory import MemorySystem
from lifeforce.memory.self_model import SelfModelStore
from lifeforce.memory.world_model import WorldModel
from lifeforce.trading.simulator import TradingSimulator
from lifeforce.trading.strategies.grid_strategy import GridStrategy
from lifeforce.trading.strategies.trend_strategy import TrendStrategy


def run_trade_cycle(
    observer: MarketObserver,
    simulator: TradingSimulator,
    world_model: WorldModel,
    trend_strategy: TrendStrategy,
    grid_strategy: GridStrategy,
) -> Dict[str, Any]:
    snapshot = observer.observe_market()
    prices = snapshot.get("prices", {})
    btc_price = float(prices.get("BTC/USDT", 0.0))
    closes = _read_recent_closes(observer.memory, "BTC/USDT", limit=120)
    closes.append(btc_price)
    trend_signal = trend_strategy.signal(closes)
    last_price = closes[-2] if len(closes) >= 2 else btc_price
    grid_signal = grid_strategy.generate_signal(btc_price, last_price)
    final_signal = trend_signal if trend_signal != "hold" else grid_signal
    trade_result = simulator.execute_signal("BTC/USDT", final_signal, btc_price, timestamp=datetime.now().isoformat())
    world_model.add_fact(
        f"交易决策 BTC/USDT: trend={trend_signal}, grid={grid_signal}, final={final_signal}",
        source="trade_daemon",
    )
    return {
        "snapshot": snapshot,
        "trend_signal": trend_signal,
        "grid_signal": grid_signal,
        "final_signal": final_signal,
        "trade_result": trade_result,
        "portfolio": simulator.stats({"BTC/USDT": btc_price}),
    }


def run_hourly_reflection(memory: MemorySystem, self_model: SelfModelStore) -> Dict[str, Any]:
    reflection = (
        "交易反思:\n"
        "1. 检查止损触发次数与仓位利用率\n"
        "2. 复盘趋势信号误判与网格信号冲突\n"
        "3. 次日策略：降低高波动时仓位上限"
    )
    memory.write({"type": "trading_reflection", "content": {"text": reflection}, "importance": 0.85})
    self_model.upsert_limitation("交易策略在极端波动行情下仍需增强")
    self_model.upsert_forming_capability("交易策略冲突协调")
    self_model.set_next_strategy(["提升高波动识别，先保命再扩收益"])
    self_model.increment_evolution_count()
    self_model.set_last_reflection(datetime.now().date().isoformat())
    return {"text": reflection}


def _read_recent_closes(memory: MemorySystem, symbol: str, limit: int = 100) -> List[float]:
    rows = memory.read(memory_type="market_snapshot", limit=limit)
    closes: List[float] = []
    for row in rows:
        content = row.get("content", {})
        prices = content.get("prices", {}) if isinstance(content, dict) else {}
        if isinstance(prices, dict) and symbol in prices:
            closes.append(float(prices[symbol]))
    closes.reverse()
    return closes
