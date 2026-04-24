import asyncio
import os
from pathlib import Path
from system.models import BrokerMessage, FileEvent
from system.components.observers.base import BaseObserver

class FileTailObserver(BaseObserver):
    async def run(self, file: str):
        Path(file).touch(exist_ok=True)
        with open(file, 'r') as f:
            f.seek(0, os.SEEK_END)
            while True:
                line = f.readline()
                if line:
                    stripped_data = line.rstrip('\n')
                    if stripped_data:
                        #type - nutné pro rekontrukci modelu při zpracování přichozí zprávy přes rabbitmq
                        await self._publish(BrokerMessage(
                            type=FileEvent.__name__,
                            data=FileEvent(
                                event="new_line",
                                path="/home/user/document.pdf",
                                data=stripped_data,
                                prompt=self.prompt,
                            ),
                        ), exchange=self.exchange, queue=self.exchange, routing_key=self.routing_key)
                else:
                    await asyncio.sleep(0.1)

Observer = FileTailObserver