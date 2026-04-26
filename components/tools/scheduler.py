import os
from pydantic_ai import RunContext, Tool
from pydantic import BaseModel, Field
from system.constants import TASKS_FILE

class SchedulerParams(BaseModel):
    interval: str = Field(description="Cron syntaxe intervalu opakujícího se úkolu")
    prompt: str = Field(description="Prompt pro AI opakujícího se úkolu. Drž se přesně požadavku.")

class SchedulerResult(BaseModel):
    success: bool = Field(description="Zda byla zpráva úspěšně odeslána")

def scheduler(ctx: RunContext, params: SchedulerParams) -> SchedulerResult:

    with open(TASKS_FILE, mode='a', encoding='utf-8') as f:
        f.write(f"{params.interval}|{params.prompt}\n")

    return SchedulerResult(
        success=True
    )

tool = Tool(scheduler, description="Uložení opakující se úkolu.")
