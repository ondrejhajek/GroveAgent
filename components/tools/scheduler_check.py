from pydantic_ai import RunContext, Tool
from pydantic import BaseModel, Field


class SchedulerCheckResult(BaseModel):
    scheduled_tasks: str = Field(description="Seznam uložených opakujících se úkolů")

def scheduler_check(ctx: RunContext) -> SchedulerCheckResult:

    data = """*/1 * * * *|pošli mi email s předmětem Ahoj
           """

    return SchedulerCheckResult(
        scheduled_tasks=data
    )

tool = Tool(scheduler_check, description="Zjištění jestli už opakujících se úloha existuje.")
