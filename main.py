import os, logfire, yaml
from pathlib import Path
from typing import Dict
from pydantic_ai import ModelRequest, UserPromptPart
from faststream import FastStream
from faststream.rabbit import ExchangeType, RabbitBroker, RabbitExchange, RabbitQueue, RabbitMessage
from contextlib import asynccontextmanager
from fastapi import FastAPI
from system import models
from system.agent import create_agent, AgentConfig
from system.observers import bootstrap_observers
from system.helpers import load_or_create_agent_id, print_startup_banner
from jinja2 import Template
from dotenv import load_dotenv
load_dotenv()

logfire.configure()
logfire.instrument_pydantic_ai()
from system.constants import BASE_DIR, CONFIG_FILE, MEMORY_FILE, STORAGE_DIR

with open(CONFIG_FILE) as f:
    tpl = Template(f.read())

rendered = tpl.render(
    BASE_DIR=BASE_DIR,
    MEMORY_FILE=MEMORY_FILE,
    STORAGE_DIR=STORAGE_DIR
)

config_data = yaml.safe_load(rendered)

agent_config = config_data.get("agent", [{}])[0]

AGENT_ID = load_or_create_agent_id(agent_config.get("nickname"))

print_startup_banner(AGENT_ID, config_data, os.environ.get("RABBITMQ_HOST", ""), os.environ.get("RABBITMQ_USERNAME", ""))

broker = RabbitBroker(f"amqp://{os.environ['RABBITMQ_USERNAME']}:{os.environ['RABBITMQ_PASSWORD']}@{os.environ["RABBITMQ_HOST"]}/")

faststream = FastStream(broker)

exchange = RabbitExchange(AGENT_ID, durable=True, auto_delete=False, type=ExchangeType.TOPIC)

observers = config_data.get('observers', {})

# with open(file_path, "r", encoding="utf-8") as f:
#     for line in f:
#         line = line.strip()
#         if not line:
#             continue
#         try:
#             prompt, cron = line.split("@", 1)
#         except ValueError:
#             continue
#         observers.append(
#             {
#                 "enabled": True,
#                 "type": "cron",
#                 "parameters": {
#                     "interval": cron.strip()
#                 },
#                 "prompt": prompt.strip()
#             }
#         )

@faststream.on_startup
async def on_startup():
    await bootstrap_observers(config_data.get('observers', []), broker, exchange, AGENT_ID)
    # await bootstrap_tasker(config_data.get('observers', []), broker, exchange, AGENT_ID)

agent = create_agent(
    AgentConfig(
        name=agent_config.get("name"),
        model_name=agent_config.get("model"),
        tools_agents=config_data.get("tools_agents", []),
        mcp=agent_config.get("mcp"),
        instructions=agent_config.get("instructions", ""),
        tools=agent_config.get("tools", []),
    )
)

@broker.subscriber(RabbitQueue(AGENT_ID, routing_key=AGENT_ID), exchange=exchange)
async def handle_data(msg: Dict, message: RabbitMessage):
    model_type = msg.get("type")
    payload = msg.get("data")
    modeled_data = models.get_model_instance(model_type, payload)
    if modeled_data:
        await agent.run(
            modeled_data.prompt,
            message_history=[#Zjednodušeně: prompt říká co se ptáme, a message_history dodá strukturovaná data, nad kterými má agent uvažovat
                ModelRequest(parts=[
                    UserPromptPart(content=modeled_data.model_dump_json())
                ])
            ]
        )
    else:
        print(f"Chyba: Model {model_type} nebyl nalezen v models.py")

@asynccontextmanager
async def lifespan(fastapi: FastAPI):
    # Kód zde se provede při STARTU aplikace
    print("Starting FastStream broker...")
    await faststream._startup()
    try:
        yield
    finally:
        print("Shutting down FastStream broker...")
        await faststream._shutdown()

app = agent.to_web()

app.router.lifespan_context = lifespan
