from dataclasses import asdict

from quart import Blueprint, websocket

from log import logger

from service.structures import PluginInfo

Bp = Blueprint('ws:status', __name__, url_prefix='/ws/status')


@Bp.websocket('/')
async def connection():
    client_info = PluginInfo(name='plugin', version='0.0.1')
    data = (await websocket.receive_json())
    if isinstance(data, dict):
        try:
            client_info = PluginInfo(**data)
        except TypeError as e:
            logger.debug("Bad PluginInfo: {e}", e=e)
            await websocket.close(1008, 'Bad PluginINfo')
            return
    else:
        await websocket.close(1008, )
    await websocket.send_json(asdict(client_info))
