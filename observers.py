import asyncio
import importlib
import threading
from faststream.rabbit import RabbitBroker, RabbitExchange

async def bootstrap_observers(observers: dict, broker: RabbitBroker, exchange: RabbitExchange, app_id: str):
    main_loop = asyncio.get_running_loop()
    for item in observers:
        if item.get("enabled", False):
            params = item.get("parameters", {})
            observer_module = importlib.import_module(f"system.components.observers.{item.get("type")}")
            observer_class = getattr(observer_module, "Observer")
            observer = observer_class(
                broker,
                exchange=exchange,
                routing_key=app_id,
                prompt=item.get("prompt"),
            )
            observer._main_loop = main_loop
            thread = threading.Thread(
                target=lambda obs=observer, p=params: asyncio.run(obs.run(**p)),
                daemon=True,
            )
            thread.start()
