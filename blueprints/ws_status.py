import asyncio
import uuid

from quart import Blueprint, websocket

from log import logger
from service.manager import PluginService
from service.structures import ClientInfo

Bp = Blueprint('ws:status', __name__, url_prefix='/ws/status')


@Bp.websocket('/')
async def connection():
    client_info = ClientInfo(sid=uuid.UUID('00000000-0000-0000-0000-000000000000'), name='plugin', version='0.0.1')
    data = (await websocket.receive_json())
    if isinstance(data, dict):
        try:
            client_info = ClientInfo(**data)
        except TypeError as e:
            logger.debug("Bad PluginInfo: {e}", e=e)
            await websocket.close(1008, 'Bad PluginInfo')
            return
    else:
        await websocket.close(1008, 'Bad PluginInfo')

    service = PluginService(client_info.sid)
    client_info.sid = service.sid  # sync sid

    await service.add_client().process(websocket)
