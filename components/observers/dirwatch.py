import asyncio
from pathlib import Path
import watchdog.observers
from watchdog.events import FileSystemEventHandler
from system.components.observers.base import BaseObserver
from system.models import BrokerMessage, DirWatchEvent

class DirWatchObserver(BaseObserver):
    def __init__(self, broker, exchange, routing_key, prompt):
        super().__init__(broker, exchange, routing_key, prompt)
        self.running = True

    async def run(self, directory: str, extension: str):
        ext = extension if extension.startswith(".") else f".{extension}"
        obs: BaseObserver = self
        class Handler(FileSystemEventHandler):
            def on_created(self, event):
                if not event.is_directory and Path(event.src_path).suffix == ext:
                    try:
                        obs._publish_sync(
                            BrokerMessage(
                                type=DirWatchEvent.__name__,
                                data=DirWatchEvent(
                                    path=event.src_path,
                                    extension=ext,
                                    prompt=obs.prompt,
                                ),
                            ),
                            exchange=obs.exchange,
                            queue=obs.exchange,
                            routing_key=obs.routing_key,
                        )
                        print(f"Publikace proběhla úspěšně")
                    except Exception as exc:
                        print(f"Publikace selhala s chybou: {exc}")
        observer = watchdog.observers.Observer()
        observer.schedule(Handler(), directory, recursive=False)
        observer.start()
        while self.running:
            await asyncio.sleep(1)


Observer = DirWatchObserver