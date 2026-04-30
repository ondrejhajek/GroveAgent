# system/tasker.py
import os
import json
import time
import asyncio
import threading
from datetime import datetime
from croniter import croniter
from system.constants import TASKS_FILE
from system.logger import logger

class Tasker:
    def __init__(self, agent):
        self.agent = agent
        self.tasks = []
        self.next_run = {}
        self.file_mtime = 0
        self.stop_event = threading.Event()

    # -------------------------
    # LOAD
    # -------------------------
    def load_tasks(self):
        try:
            with open(TASKS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
        except FileNotFoundError:
            data = {"tasks": []}

        self.tasks = data.get("tasks", [])

        now = datetime.now()
        self.next_run = {
            self._task_id(t): croniter(t["cron"], now).get_next(datetime)
            for t in self.tasks
            if t.get("enabled", True)
        }

    def _task_id(self, task):
        return task.get("id") or (task["cron"] + task["text"])

    # -------------------------
    # FILE CHANGE CHECK
    # -------------------------
    def file_changed(self):
        try:
            mtime = os.path.getmtime(TASKS_FILE)
        except FileNotFoundError:
            return False

        if mtime != self.file_mtime:
            self.file_mtime = mtime
            return True

        return False

    # -------------------------
    # EXECUTION
    # -------------------------
    def run_task(self, task):
        logger.info("Running task: %s", task['text'])
        asyncio.run(self.agent.run(task['text']))

    # -------------------------
    # LOOP
    # -------------------------
    def loop(self):
        self.load_tasks()

        while not self.stop_event.is_set():
            now = datetime.now()

            # reload pokud změna souboru
            if self.file_changed():
                self.load_tasks()

            # kontrola tasků
            for task in self.tasks:
                if not task.get("enabled", True):
                    continue

                task_id = self._task_id(task)

                if self.next_run.get(task_id, now) <= now:
                    self.run_task(task)

                    self.next_run[task_id] = croniter(
                        task["cron"], now
                    ).get_next(datetime)

            time.sleep(1)

    # -------------------------
    # START
    # -------------------------
    def start(self):
        threading.Thread(target=self.loop, daemon=True).start()