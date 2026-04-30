import os, logfire, yaml
import socket
import sys
from typing import Dict
from pydantic_ai import ModelRequest, UserPromptPart
from faststream import FastStream
from faststream.rabbit import ExchangeType, RabbitBroker, RabbitExchange, RabbitQueue, RabbitMessage
from contextlib import asynccontextmanager
from fastapi import FastAPI
from spectree import SpecTree
from system import models
from system.agent import create_agent
from system.observers import bootstrap_observers
from system.helpers import load_or_create_agent_id, print_startup_banner
from system.logger import logger, setup_logging
from system.routes import post_prompt, post_config
from dotenv import load_dotenv
from system.tasker import Tasker
from system.constants import CONFIG_FILE, AGENT_DIR
load_dotenv()
setup_logging()
logfire.configure()
logfire.instrument_pydantic_ai()

if not AGENT_DIR.exists():
    sys.exit(f"[ERROR] MISSING AGENT FOLDER: {AGENT_DIR}")

if not CONFIG_FILE.exists():
    sys.exit(f"[ERROR] MISSING CONFIG FILE: {CONFIG_FILE}")

with open(CONFIG_FILE) as f:
    configuration = yaml.safe_load(f)

AGENT_ID = load_or_create_agent_id(configuration.get("agent").get("nickname"))

agent = create_agent(CONFIG_FILE)

tasker = Tasker(agent)

tasker.start()

app = agent.to_web()

print_startup_banner(AGENT_ID, configuration)

#následně v routes dostupné přes request.app.state.XY
app.state.agent = agent
app.state.config = configuration
observers = configuration.get('observers', {})

if any(o.get("enabled") is True for o in observers):

    logger.info("At least one observer is enabled, starting RabbitMQ broker...")

    rmq_host = os.environ["RABBITMQ_HOST"]
    rmq_port = int(os.environ["RABBITMQ_PORT"])
    try:
        with socket.create_connection((rmq_host, rmq_port), timeout=5.0):
            pass
    except OSError as exc:
        sys.exit(f"[ERROR] RabbitMQ není dostupný na {rmq_host}:{rmq_port} ({exc})")

    broker = RabbitBroker(f"amqp://{os.environ['RABBITMQ_USERNAME']}:{os.environ['RABBITMQ_PASSWORD']}@{os.environ["RABBITMQ_HOST"]}:{os.environ["RABBITMQ_PORT"]}/")
    app.state.broker = broker
    faststream = FastStream(broker)
    exchange = RabbitExchange(AGENT_ID, durable=True, auto_delete=False, type=ExchangeType.TOPIC)

    @faststream.on_startup
    async def on_startup():
        await bootstrap_observers(configuration.get('observers', []), broker, exchange, AGENT_ID)

    @broker.subscriber(RabbitQueue(AGENT_ID, routing_key=AGENT_ID), exchange=exchange)
    async def handle_data(msg: Dict, message: RabbitMessage):
        model_type = msg.get("type")
        payload = msg.get("data")
        modeled_data = models.get_model_instance(model_type, payload)
        if modeled_data:
            await agent.run(
                modeled_data.prompt,
                message_history=[
                    # Zjednodušeně: prompt říká co se ptáme, a message_history dodá strukturovaná data, nad kterými má agent uvažovat
                    ModelRequest(parts=[
                        UserPromptPart(content=modeled_data.model_dump_json())
                    ])
                ]
            )
        else:
            logger.error("Model %s uvedený ve zprávě z brokera nebyl nalezen v models.py", model_type)

    @asynccontextmanager
    async def lifespan(fastapi: FastAPI):
        # Kód zde se provede při STARTU aplikace
        logger.info("Starting FastStream broker...")
        await faststream._startup()
        try:
            yield
        finally:
            logger.info("Shutting down FastStream broker...")
            await faststream._shutdown()

    app.router.lifespan_context = lifespan

#všechny GET routy má agent.to_web() starlett server obsazené
app.router.add_route('/agent/prompt', post_prompt, methods=['POST'])
app.router.add_route('/agent/config', post_config, methods=['POST'])

#na url /apidoc/swagger zpřístupní dokumentaci a openapi json
spec = SpecTree("starlette")

spec.register(app)
