from pathlib import Path
import yaml
from system.prompts import AGENT_BUILTIN_PROMPT
from jinja2 import Template
from system.constants import BASE_DIR, MEMORY_FILE, STORAGE_DIR, TASKS_FILE
from pydantic_ai import Agent, FunctionToolset
from dataclasses import dataclass, field
from typing import List, Any, Dict
from pydantic_ai.models.openrouter import OpenRouterModel
from pydantic_ai.providers.openrouter import OpenRouterProvider
from pydantic_ai.toolsets.fastmcp import FastMCPToolset
import os, importlib
from dotenv import load_dotenv
load_dotenv()

@dataclass
class AgentConfig:
    name: str
    model_name: str
    instructions: str
    tools_agents: Dict[str, Any]
    mcpServers: Dict[str, Any]
    mcp: List[str]
    tools: List[str] = field(default_factory=list)

def create_agent(config_file) -> Agent:

    Path(STORAGE_DIR).mkdir(parents=True, exist_ok=True)

    with open(MEMORY_FILE, "a", encoding="utf-8"):
        pass
    with open(TASKS_FILE, "w", encoding="utf-8") as f:
        f.write("{}")

    with open(config_file) as f:
        tpl = Template(f.read())

    rendered = tpl.render(
        BASE_DIR=BASE_DIR,
        MEMORY_FILE=MEMORY_FILE,
        STORAGE_DIR=STORAGE_DIR
    )

    config_data = yaml.safe_load(rendered)

    agent_config = config_data.get("agent")

    agent_config = AgentConfig(
        name=agent_config.get("name"),
        model_name=agent_config.get("model"),
        tools_agents=config_data.get("tools_agents", []),
        mcpServers=agent_config.get("mcpServers"),
        mcp=agent_config.get("mcp"),
        instructions=AGENT_BUILTIN_PROMPT.replace('{{MEMORY_FILE}}', str(MEMORY_FILE)) + agent_config.get("instructions", ""),
        tools=agent_config.get("tools", [])
    )

    model = OpenRouterModel(
        agent_config.model_name,
        provider=OpenRouterProvider(
            api_key=os.environ['OPENROUTER_API_KEY']
        )
    )

    toolsets = build_toolsets(agent_config.mcpServers, agent_config.mcp, agent_config.tools_agents, agent_config.tools)

    return Agent(
        model,
        instructions=agent_config.instructions,
        toolsets=toolsets
    )

def build_toolsets(mcp_servers, mcps, tools_agents, tools: List[str] = None) -> List[FunctionToolset]:

    toolsets = []

    if mcp_servers:
        toolsets.append(FastMCPToolset(mcp_servers))

    mcps = list(dict.fromkeys(mcps + ["tasks"])) #vždy spouštět "tasks" mcp

    if mcps:
        for name in mcps:
            try:
                module = importlib.import_module(f"components.mcps.{name}")
            except ModuleNotFoundError:
                module = importlib.import_module(f"system.components.mcps.{name}")
            toolsets.append(FastMCPToolset(module.mcp))

    if tools:
        component_tools = []
        for name in tools:
            try:
                module = importlib.import_module(f"components.tools.{name}")
                component_tools.append(module.tool)
            except ModuleNotFoundError:
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