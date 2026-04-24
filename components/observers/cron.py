import asyncio
from datetime import datetime, timezone
from croniter import croniter
from system.models import BrokerMessage, CronEvent
from system.components.observers.base import BaseObserver

class CronObserver(BaseObserver):
    async def run(self, interval: str):
        itr = croniter(interval, datetime.now(timezone.utc))
        while True:
            next_fire = itr.get_next(datetime)
            delay = (next_fire - datetime.now(timezone.utc)).total_seconds()
            if delay > 0:
                await asyncio.sleep(delay)
            await self._publish(
                BrokerMessage(
                    type=CronEvent.__name__,
                    data=CronEvent(
                        interval=interval,
                        fired_at=datetime.now(timezone.utc).isoformat(),
                        current_time=datetime.now().strftime("%-d. %-m. %Y, %H:%M, %A"),
                        prompt=self.prompt,
                    ),
                ),
                exchange=self.exchange,
                routing_key=self.routing_key,
            )


Observer = CronObserver