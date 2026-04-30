from mcp.server.fastmcp import FastMCP
from system.constants import TASKS_FILE
from pydantic import BaseModel
from typing import List
import json

class Task(BaseModel):
    cron: str
    text: str

class TasksResponse(BaseModel):
    tasks: List[Task]

class SaveTasksRequest(BaseModel):
    tasks: List[Task]

class SaveTasksResponse(BaseModel):
    status: str

mcp = FastMCP(
    name="Tasks",
    instructions="""
                Správa plánovaných úloh.

                Každá úloha má:
                - cron (čas vykonání) - pokud jde o úkol typu: za XY minut/hodin/dnů, zjisti si aktální čas a požadovaný čas ulož do cron formátu
                - text (prompt pro LLM)
                
                Pracovní postup:
                1. Vždy zavolej get_tasks
                2. Uprav seznam úloh jako strukturovaný JSON objekt, přidej tasky které bys měl přidat a nebo osztraň ty které již nemají být naplánované.
                3. Ulož přes save_tasks
                
                DŮLEŽITÉ:
                - Používej vždy strukturovaná data (JSON schema)
                - Nikdy nepracuj s CRON|TEXT stringy přímo
                """
)

@mcp.tool()
def get_tasks() -> TasksResponse:
    """Vrátí seznam naplánovaných úloh."""
    try:
        with open(TASKS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        return TasksResponse(tasks=[])

    tasks = [Task(**item) for item in data.get("tasks", [])]

    return TasksResponse(tasks=tasks)


@mcp.tool()
def save_tasks(data: SaveTasksRequest) -> SaveTasksResponse:
    """Uloží seznam úloh jako JSON."""

    payload = {
        "tasks": [t.model_dump() for t in data.tasks]
    }

    with open(TASKS_FILE, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    return SaveTasksResponse(status="ok")
