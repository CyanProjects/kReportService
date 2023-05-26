import uuid

from dataclasses import asdict
from quart import Blueprint, websocket

from log import logger
from service.manager import PluginService
from service.structures import ClientInfo

Bp = Blueprint('ws:status', __name__, url_prefix='/ws')


@Bp.websocket('/status/<plugin:plugin>')
async def connection_plugin(plugin: PluginService):
    client_info = ClientInfo(**asdict(plugin.plugin_info))
    data = (await websocket.receive_json())
    if isinstance(data, dict):
        plugin_default_info = asdict(client_info)
        data.update(plugin_default_info)
        try:
            client_info = ClientInfo(**data)
        except TypeError as e:
            logger.debug("Bad ClientInfo")
            await websocket.close(1008, 'Bad ClientInfo')
            return
    else:
        await websocket.close(1008, 'Bad ClientInfo')
        return

    await plugin.add_client(client_info=client_info).process(websocket)


@Bp.websocket('/status')
async def connection():
    client_info = ClientInfo(sid=uuid.UUID('00000000-0000-0000-0000-000000000000'))
    data = (await websocket.receive_json())
    if isinstance(data, dict):
        try:
            client_info = ClientInfo(**data)
        except TypeError as e:
            logger.debug("Bad ClientInfo: {e}", e=e)
            await websocket.close(1008, 'Bad ClientInfo')
            return
    else:
        await websocket.close(1008, 'Bad ClientInfo')
        return

    plugin = PluginService(sid=client_info.sid, name=client_info.name)
    client_info.sid = plugin.sid  # sync sid

    await plugin.add_client().process(websocket)
