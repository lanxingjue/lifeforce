"""简单消息总线。"""

from collections import defaultdict
from typing import Any, Callable, DefaultDict, List


class MessageBus:
    def __init__(self) -> None:
        self._handlers: DefaultDict[str, List[Callable[[Any], None]]] = defaultdict(list)

    def subscribe(self, topic: str, handler: Callable[[Any], None]) -> None:
        self._handlers[topic].append(handler)

    def publish(self, topic: str, payload: Any) -> None:
        for handler in self._handlers[topic]:
            handler(payload)
