import importlib
from pydantic_ai import Agent, FunctionToolset
from dataclasses import dataclass, field
from typing import List, Any, Dict
from pydantic_ai.models.openrouter import OpenRouterModel
from pydantic_ai.providers.openrouter import OpenRouterProvider
from pydantic_ai.toolsets.fastmcp import FastMCPToolset
import os

@dataclass
class AgentConfig:
    name: str
    model_name: str
    instructions: str
    tools_agents: Dict[str, Any]
    mcp: Dict[str, Any]
    tools: List[str] = field(default_factory=list)

def create_agent(cfg: AgentConfig) -> Agent:

    model = OpenRouterModel(
        cfg.model_name,
        provider=OpenRouterProvider(
            api_key=os.environ['OPENROUTER_API_KEY']
        )
    )

    toolsets = build_toolsets(cfg.mcp, cfg.tools_agents, cfg.tools)

    return Agent(
        model,
        instructions=cfg.instructions,
        toolsets=toolsets,
    )

def build_toolsets(mcp, tools_agents, tools: List[str] = None) -> List[FunctionToolset]:

    toolsets = []

    if mcp:
        toolsets.append(FastMCPToolset(mcp))

    if tools:
        component_tools = []
        for name in tools:
            module = importlib.import_module(f"system.components.tools.{name}")
            component_tools.append(module.tool)
        toolsets.append(FunctionToolset(component_tools))

    toolset_agents = FunctionToolset()

    for tools_agent_config in tools_agents:

        if not tools_agent_config.get("enabled", False):
            continue

        tools_agents_model = OpenRouterModel(
            tools_agent_config.get("model"),
            provider=OpenRouterProvider(
                api_key=os.environ['OPENROUTER_API_KEY'],
            ),
        )

        tools_agents_agent = Agent(
            tools_agents_model,
            instructions=tools_agent_config.get("instructions", ""),
        )

        def make_tools_agents_tool(sa: Agent, parameters_doc):
            async def tools_agents_tool(prompt: str) -> str:
                result = await sa.run(prompt)
                return result.output
            tools_agents_tool.__doc__ = parameters_doc
            return tools_agents_tool

        toolset_agents.add_function(
            make_tools_agents_tool(tools_agents_agent, tools_agent_config.get("parameters_doc")),
            name=tools_agent_config.get("name"),
            description=tools_agent_config.get("tool_description", ""),
            takes_ctx=False,
            docstring_format="google"
        )

    toolsets.append(toolset_agents)

    return toolsets