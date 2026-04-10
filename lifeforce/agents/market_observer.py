"""市场观察者 Agent。"""

from datetime import datetime
import time
from typing import Any, Dict, List, Optional

import httpx

from lifeforce.core.agent import Agent
from lifeforce.core.budget import BudgetGuard
from lifeforce.core.memory import MemorySystem

try:
    import ccxt  # type: ignore
except Exception:  # pragma: no cover
    ccxt = None


class MarketObserver(Agent):
    """监控市场价格与 K 线数据并写入记忆。"""

    def __init__(
        self,
        memory: MemorySystem,
        budget_guard: BudgetGuard,
        exchange_id: str = "binance",
        symbols: Optional[List[str]] = None,
        exchange: Any = None,
    ) -> None:
        super().__init__(name="MarketObserver", role="监控市场数据", memory=memory, budget_guard=budget_guard)
        self.symbols = symbols or ["BTC/USDT", "ETH/USDT"]
        self.exchange = exchange if exchange is not None else self._build_exchange(exchange_id)

    def _build_exchange(self, exchange_id: str) -> Any:
        if ccxt is None:
            return _HttpBinanceExchange()
        exchange_class = getattr(ccxt, exchange_id)
        return exchange_class({"enableRateLimit": True, "options": {"defaultType": "spot"}})

    def fetch_prices(self) -> Dict[str, float]:
        if hasattr(self.exchange, "fetch_prices"):
            try:
                batch = self.exchange.fetch_prices(self.symbols)
                if isinstance(batch, dict) and batch:
                    return {symbol: float(batch.get(symbol, 0.0)) for symbol in self.symbols}
            except Exception as exc:
                self.logger.warning("批量 fetch_prices 失败，降级单 symbol 获取: %s", exc)
        prices: Dict[str, float] = {}
        for symbol in self.symbols:
            try:
                ticker = self.exchange.fetch_ticker(symbol)
            except Exception as exc:
                self.logger.warning("交易所 fetch_ticker 失败，切换 HTTP 兜底: %s", exc)
                self.exchange = _HttpBinanceExchange()
                ticker = self.exchange.fetch_ticker(symbol)
            prices[symbol] = float(ticker.get("last", 0.0))
        return prices

    def fetch_ohlcv(self, symbol: str, timeframe: str = "1h", limit: int = 100) -> List[List[float]]:
        try:
            rows = self.exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
        except Exception as exc:
            self.logger.warning("交易所 fetch_ohlcv 失败，切换 HTTP 兜底: %s", exc)
            self.exchange = _HttpBinanceExchange()
            rows = self.exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
        return [[float(item) for item in row] for row in rows]

    def observe_market(self) -> Dict[str, Any]:
        prices = self.fetch_prices()
        snapshot = {"type": "market_snapshot", "prices": prices, "timestamp": datetime.now().isoformat()}
        self.memory.write({"type": "market_snapshot", "content": snapshot, "importance": 0.6})
        self.log_action("observe_market", {"symbols": self.symbols, "prices": prices})
        return snapshot

    def process(self, message: Dict[str, Any]) -> Dict[str, Any]:
        command = str(message.get("command", "observe"))
        if command == "observe":
            return self.observe_market()
        if command == "get_prices":
            return {"prices": self.fetch_prices()}
        if command == "get_ohlcv":
            symbol = str(message.get("symbol", "BTC/USDT"))
            timeframe = str(message.get("timeframe", "1h"))
            limit = int(message.get("limit", 100))
            return {"symbol": symbol, "timeframe": timeframe, "ohlcv": self.fetch_ohlcv(symbol, timeframe, limit)}
        return {"error": f"Unknown command: {command}"}


class _HttpBinanceExchange:
    _cached_prices: Dict[str, float] = {}
    _cached_at: float = 0.0
    _cache_ttl_seconds: int = 25

    def fetch_prices(self, symbols: List[str]) -> Dict[str, float]:
        result: Dict[str, float] = {}
        now = time.time()
        if self._cached_prices and now - self._cached_at < self._cache_ttl_seconds:
            for symbol in symbols:
                if symbol in self._cached_prices:
                    result[symbol] = self._cached_prices[symbol]
            if len(result) == len(symbols):
                return result

        # 尝试 Binance 单价接口
        for symbol in symbols:
            market = symbol.replace("/", "")
            try:
                response = httpx.get(
                    "https://api.binance.com/api/v3/ticker/price",
                    params={"symbol": market},
                    timeout=20.0,
                )
                response.raise_for_status()
                data = response.json()
                result[symbol] = float(data.get("price", 0.0))
            except Exception:
                continue
        if len(result) == len(symbols):
            self._cached_prices = dict(result)
            self._cached_at = now
            return result

        # Binance 不可用时，批量走 CoinGecko，避免逐 symbol 触发 429
        gecko = self._fetch_coingecko_prices(symbols)
        result.update(gecko)
        if result:
            self._cached_prices = dict(result)
            self._cached_at = now
            return result

        if self._cached_prices:
            return {symbol: float(self._cached_prices.get(symbol, 0.0)) for symbol in symbols}
        raise RuntimeError("无法获取市场价格（Binance/CoinGecko 均失败）")

    def fetch_ticker(self, symbol: str) -> Dict[str, float]:
        market = symbol.replace("/", "")
        try:
            response = httpx.get("https://api.binance.com/api/v3/ticker/price", params={"symbol": market}, timeout=20.0)
            response.raise_for_status()
            data = response.json()
            return {"last": float(data.get("price", 0.0))}
        except Exception:
            gecko = self._fetch_coingecko_prices([symbol])
            if symbol in gecko:
                return {"last": gecko[symbol]}
            if symbol in self._cached_prices:
                return {"last": float(self._cached_prices[symbol])}
            raise

    def fetch_ohlcv(self, symbol: str, timeframe: str = "1h", limit: int = 100) -> List[List[float]]:
        market = symbol.replace("/", "")
        interval_map = {"1m": "1m", "5m": "5m", "15m": "15m", "1h": "1h", "4h": "4h", "1d": "1d"}
        interval = interval_map.get(timeframe, "1h")
        try:
            response = httpx.get(
                "https://api.binance.com/api/v3/klines",
                params={"symbol": market, "interval": interval, "limit": limit},
                timeout=20.0,
            )
            response.raise_for_status()
            rows = response.json()
            return [[float(item) for item in row[:6]] for row in rows]
        except Exception:
            coin = "bitcoin" if market.startswith("BTC") else "ethereum"
            response = httpx.get(
                f"https://api.coingecko.com/api/v3/coins/{coin}/ohlc",
                params={"vs_currency": "usd", "days": 7},
                timeout=20.0,
            )
            response.raise_for_status()
            rows = response.json()
            converted: List[List[float]] = []
            for row in rows[-limit:]:
                ts, open_price, high, low, close = row
                converted.append([float(ts), float(open_price), float(high), float(low), float(close), 0.0])
            return converted

    def _fetch_coingecko_prices(self, symbols: List[str]) -> Dict[str, float]:
        symbol_to_id = {"BTC/USDT": "bitcoin", "ETH/USDT": "ethereum"}
        ids = [symbol_to_id[symbol] for symbol in symbols if symbol in symbol_to_id]
        if not ids:
            return {}
        response = httpx.get(
            "https://api.coingecko.com/api/v3/simple/price",
            params={"ids": ",".join(ids), "vs_currencies": "usd"},
            timeout=20.0,
        )
        response.raise_for_status()
        data = response.json()
        result: Dict[str, float] = {}
        for symbol in symbols:
            coin_id = symbol_to_id.get(symbol)
            if not coin_id:
                continue
            price = data.get(coin_id, {}).get("usd")
            if price is not None:
                result[symbol] = float(price)
        return result
