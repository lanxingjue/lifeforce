from lifeforce.agents.market_observer import MarketObserver, _HttpBinanceExchange
from lifeforce.core.budget import BudgetGuard
from lifeforce.core.memory import MemorySystem


class FakeExchange:
    def fetch_ticker(self, symbol: str):
        prices = {"BTC/USDT": 70000.0, "ETH/USDT": 3500.0}
        return {"last": prices.get(symbol, 0.0)}

    def fetch_ohlcv(self, symbol: str, timeframe: str = "1h", limit: int = 100):
        return [[1, 2, 3, 4, 5, 6] for _ in range(limit)]


class BrokenExchange:
    def fetch_ticker(self, symbol: str):
        raise RuntimeError("binance exchangeInfo error")

    def fetch_ohlcv(self, symbol: str, timeframe: str = "1h", limit: int = 100):
        raise RuntimeError("binance klines error")


def test_market_observer_fetch_and_write(tmp_path) -> None:
    memory = MemorySystem(str(tmp_path / "market.db"), config={"data_dir": str(tmp_path)})
    observer = MarketObserver(
        memory=memory,
        budget_guard=BudgetGuard(),
        symbols=["BTC/USDT", "ETH/USDT"],
        exchange=FakeExchange(),
    )
    prices = observer.fetch_prices()
    assert prices["BTC/USDT"] == 70000.0
    snapshot = observer.observe_market()
    assert "prices" in snapshot
    written = memory.read(memory_type="market_snapshot", limit=5)
    assert written
    memory.close()


def test_market_observer_runtime_fallback(monkeypatch, tmp_path) -> None:
    memory = MemorySystem(str(tmp_path / "market_fallback.db"), config={"data_dir": str(tmp_path)})
    observer = MarketObserver(memory=memory, budget_guard=BudgetGuard(), exchange=BrokenExchange())
    monkeypatch.setattr("lifeforce.agents.market_observer._HttpBinanceExchange.fetch_ticker", lambda self, symbol: {"last": 123.0})
    prices = observer.fetch_prices()
    assert prices["BTC/USDT"] == 123.0
    memory.close()


def test_http_exchange_use_cached_prices_when_rate_limited(monkeypatch) -> None:
    exchange = _HttpBinanceExchange()

    class _Resp:
        def __init__(self, payload, raise_http=False):
            self._payload = payload
            self._raise_http = raise_http

        def raise_for_status(self):
            if self._raise_http:
                raise RuntimeError("429")

        def json(self):
            return self._payload

    calls = {"count": 0}

    def _mock_get(url, params=None, timeout=20.0):
        _ = timeout
        if "binance.com" in url:
            raise RuntimeError("binance blocked")
        calls["count"] += 1
        if calls["count"] == 1:
            return _Resp({"bitcoin": {"usd": 71000.0}, "ethereum": {"usd": 3500.0}})
        return _Resp({}, raise_http=True)

    monkeypatch.setattr("lifeforce.agents.market_observer.httpx.get", _mock_get)
    first = exchange.fetch_prices(["BTC/USDT", "ETH/USDT"])
    second = exchange.fetch_prices(["BTC/USDT", "ETH/USDT"])
    assert first["BTC/USDT"] == 71000.0
    assert second["BTC/USDT"] == 71000.0
