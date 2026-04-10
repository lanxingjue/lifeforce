"""模拟交易器。"""

from datetime import datetime
import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from lifeforce.core.memory import MemorySystem
from lifeforce.memory.world_model import WorldModel


class TradingSimulator:
    """模拟买卖、手续费、仓位与盈亏。"""

    def __init__(
        self,
        initial_cash: float = 1000.0,
        fee_rate: float = 0.001,
        max_position_pct: float = 0.3,
        stop_loss_pct: float = 0.05,
        memory: Optional[MemorySystem] = None,
        world_model: Optional[WorldModel] = None,
        state_path: Optional[Path] = None,
    ) -> None:
        self.cash = initial_cash
        self.fee_rate = fee_rate
        self.max_position_pct = max_position_pct
        self.stop_loss_pct = stop_loss_pct
        self.positions: Dict[str, Dict[str, float]] = {}
        self.trade_history: List[Dict[str, Any]] = []
        self.memory = memory
        self.world_model = world_model or WorldModel()
        self.state_path = state_path
        if self.state_path is not None and self.state_path.exists():
            self._load_state()

    def _load_state(self) -> None:
        assert self.state_path is not None
        raw = json.loads(self.state_path.read_text(encoding="utf-8"))
        if isinstance(raw, dict):
            self.cash = float(raw.get("cash", self.cash))
            positions = raw.get("positions", {})
            if isinstance(positions, dict):
                self.positions = {
                    str(k): {
                        "amount": float(v.get("amount", 0.0)),
                        "entry_price": float(v.get("entry_price", 0.0)),
                    }
                    for k, v in positions.items()
                    if isinstance(v, dict)
                }
            history = raw.get("trade_history", [])
            if isinstance(history, list):
                self.trade_history = [item for item in history if isinstance(item, dict)]

    def _save_state(self) -> None:
        if self.state_path is None:
            return
        self.state_path.parent.mkdir(parents=True, exist_ok=True)
        self.state_path.write_text(
            json.dumps(
                {"cash": self.cash, "positions": self.positions, "trade_history": self.trade_history[-200:]},
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

    def _record(self, item: Dict[str, Any]) -> None:
        self.trade_history.append(item)
        self._save_state()
        if self.memory is not None:
            self.memory.write({"type": "trade_event", "content": item, "importance": 0.7})

    def _position_value(self, symbol: str, price: float) -> float:
        pos = self.positions.get(symbol)
        if not pos:
            return 0.0
        return float(pos["amount"]) * price

    def _apply_stop_loss(self, symbol: str, price: float, timestamp: str) -> Optional[Dict[str, Any]]:
        pos = self.positions.get(symbol)
        if not pos:
            return None
        entry = float(pos["entry_price"])
        if entry <= 0:
            return None
        drawdown = (entry - price) / entry
        if drawdown < self.stop_loss_pct:
            return None
        return self.sell(symbol, price, float(pos["amount"]), timestamp, reason="stop_loss")

    def buy(self, symbol: str, price: float, amount: float, timestamp: str, reason: str = "signal_buy") -> Dict[str, Any]:
        max_value = self.cash * self.max_position_pct
        order_value = min(max_value, price * amount)
        if order_value <= 0:
            return {"status": "rejected", "reason": "no_cash"}
        actual_amount = order_value / price
        fee = order_value * self.fee_rate
        total_cost = order_value + fee
        if total_cost > self.cash:
            return {"status": "rejected", "reason": "insufficient_cash"}
        self.cash -= total_cost
        current = self.positions.get(symbol, {"amount": 0.0, "entry_price": price})
        total_amount = float(current["amount"]) + actual_amount
        weighted_entry = (
            (float(current["entry_price"]) * float(current["amount"]) + price * actual_amount) / total_amount
            if total_amount > 0
            else price
        )
        self.positions[symbol] = {"amount": total_amount, "entry_price": weighted_entry}
        event = {
            "timestamp": timestamp,
            "symbol": symbol,
            "side": "buy",
            "price": price,
            "amount": actual_amount,
            "fee": fee,
            "reason": reason,
            "cash_after": self.cash,
        }
        self._record(event)
        self.world_model.add_fact(f"执行买入 {symbol}，price={price:.2f}, reason={reason}", source="trade_daemon")
        return {"status": "filled", **event}

    def sell(self, symbol: str, price: float, amount: float, timestamp: str, reason: str = "signal_sell") -> Dict[str, Any]:
        pos = self.positions.get(symbol)
        if not pos or amount <= 0:
            return {"status": "rejected", "reason": "no_position"}
        sell_amount = min(amount, float(pos["amount"]))
        value = sell_amount * price
        fee = value * self.fee_rate
        proceeds = value - fee
        self.cash += proceeds
        remain = float(pos["amount"]) - sell_amount
        if remain <= 1e-9:
            self.positions.pop(symbol, None)
        else:
            self.positions[symbol] = {"amount": remain, "entry_price": float(pos["entry_price"])}
        event = {
            "timestamp": timestamp,
            "symbol": symbol,
            "side": "sell",
            "price": price,
            "amount": sell_amount,
            "fee": fee,
            "reason": reason,
            "cash_after": self.cash,
        }
        self._record(event)
        self.world_model.add_fact(f"执行卖出 {symbol}，price={price:.2f}, reason={reason}", source="trade_daemon")
        return {"status": "filled", **event}

    def execute_signal(self, symbol: str, signal: str, price: float, timestamp: Optional[str] = None) -> Dict[str, Any]:
        ts = timestamp or datetime.now().isoformat()
        stop_loss_event = self._apply_stop_loss(symbol, price, ts)
        if stop_loss_event is not None:
            self.world_model.add_risk(f"{symbol} 触发止损，price={price:.2f}", source="trade_daemon")
            return stop_loss_event
        if signal == "buy":
            return self.buy(symbol, price, amount=1.0, timestamp=ts)
        if signal == "sell":
            amount = float(self.positions.get(symbol, {}).get("amount", 0.0))
            if amount <= 0:
                return {"status": "rejected", "reason": "no_position"}
            return self.sell(symbol, price, amount=amount, timestamp=ts)
        return {"status": "hold", "symbol": symbol, "price": price, "timestamp": ts}

    def portfolio_value(self, price_map: Dict[str, float]) -> float:
        value = self.cash
        for symbol, pos in self.positions.items():
            value += float(pos["amount"]) * float(price_map.get(symbol, 0.0))
        return value

    def stats(self, price_map: Optional[Dict[str, float]] = None) -> Dict[str, Any]:
        mark = self.portfolio_value(price_map or {})
        return {
            "cash": self.cash,
            "positions": self.positions,
            "trade_count": len(self.trade_history),
            "portfolio_value": mark,
            "pnl": mark - 1000.0,
        }
