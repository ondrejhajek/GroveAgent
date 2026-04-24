import asyncio
from abc import ABC, abstractmethod
from system.models import BrokerMessage

class BaseObserver(ABC):
    def __init__(self, broker, exchange, routing_key, prompt):
        self.broker = broker
        self.exchange = exchange
        self.routing_key = routing_key
        self.prompt = prompt
        self._main_loop: asyncio.AbstractEventLoop | None = None

    # Použij v async kontextu (uvnitř async def run) — čeká na výsledek bez blokování event loopu.
    async def _publish(self, message: BrokerMessage, **kwargs):
        print("PUBLISHING " + str(message))
        future = asyncio.run_coroutine_threadsafe(
            self.broker.publish({"type": message.type, "data": message.data.model_dump()}, **kwargs),
            self._main_loop,
        )
        await asyncio.wrap_future(future)

    # Použij v sync kontextu (např. callback watchdogu) — blokuje volající vlákno až do dokončení publish.
    def _publish_sync(self, message: BrokerMessage, **kwargs):
        print("PUBLISHING " + str(message))
        future = asyncio.run_coroutine_threadsafe(
            self.broker.publish({"type": message.type, "data": message.data.model_dump()}, **kwargs),
            self._main_loop,
        )
        future.result(timeout=5.0)

    @abstractmethod
    async def run(self, *args, **kwargs):
        pass
