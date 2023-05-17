import asyncio
import signal
from typing import Any

from hypercorn.asyncio import serve
from hypercorn.config import Config
from create_app import create_app
from ever_loguru import install_handlers

install_handlers()

app = create_app()

config = Config()
config.bind = ['0.0.0.0:51490']

shutdown_event = asyncio.Event()


def _signal_handler(*_: Any) -> None:
    shutdown_event.set()


loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)
loop.add_signal_handler(signal.SIGINT, _signal_handler)
loop.add_signal_handler(signal.SIGTERM, _signal_handler)
loop.run_until_complete(
    serve(app, config, shutdown_trigger=shutdown_event.wait)
)
