import asyncio
import copy
import datetime
import pathlib
import pickle
import uuid
from asyncio import CancelledError
from dataclasses import asdict, is_dataclass

from typing import Any, Optional

try:
    from typing import Self, NotRequired, Required
except ImportError:
    from typing_extensions import Self, NotRequired, Required

from quart import Websocket, json

from log import logger
from .structures import Handler, StatusEvent, BroadcastEvent, DownEvent, event_mapping, UpEvent, \
    ReportHandler, ReportEvent, DisconnectEvent, ClientInfo, PluginInfo


class FileReportHandler(ReportHandler):
    async def emit(self, report: ReportEvent):
        path = pathlib.Path(f'./{report.sid}_report.json')
        if not path.is_file():
            with path.open('w') as fp:
                fp.write('[]')
        with path.open('r', encoding='u8') as frp:
            tmp = json.load(frp)
            with path.open('w', encoding='u8') as fwp:
                tmp.append(
                    asdict(report)
                )
                json.dump(tmp, fwp, ensure_ascii=False)


class ServiceClient:
    def __init__(self, cid: uuid.UUID, parent: "PluginService" = None, client_info: ClientInfo = None, queue_max=50):
        self.cid = cid
        self.parent_plugin: Optional["PluginService"] = parent
        if not client_info:
            client_info = ClientInfo(**asdict(self.parent_plugin.plugin_info))
        (client_info.name, client_info.sid) = \
            self.parent_plugin.plugin_info.name, self.parent_plugin.plugin_info.sid
        self.client_info = client_info
        self.count = 0
        self.up_pending_event: asyncio.Queue[UpEvent] = asyncio.Queue(queue_max)
        self.down_pending_event: asyncio.Queue[DownEvent] = asyncio.Queue(queue_max)
        self.blocker: Optional[asyncio.Barrier] = None

    async def event_receive(self):
        while True:
            event = await self.up_pending_event.get()
            await self.parent_plugin.raise_event(event)

    def add_processor(self):
        self.count += 1

    async def process(self, websocket: Websocket):
        tasks = (
            asyncio.create_task(self.send(websocket)),
            asyncio.create_task(self.receive(websocket)),
            asyncio.create_task(self.event_receive())
        )

        await asyncio.gather(*tasks)

    async def close(self):
        await self.down_pending_event.put(DisconnectEvent())
        self.blocker = asyncio.Barrier(self.count + 1)
        await self.blocker.wait()
        self.parent_plugin.clients.pop(self.cid)

    async def receive(self, websocket: Websocket):
        self.add_processor()
        await websocket.send_json(asdict(
            StatusEvent(
                sid=str(self.client_info.sid),
                cid=str(self.cid),
                name=str(self.client_info.name),
                message="Connected to server"
            )
        ))

        try:
            while True:
                if self.blocker is not None:
                    await self.blocker.wait()
                    return
                event_data: dict = await websocket.receive_json()
                event_type = event_data['type']
                event_data.pop('type')
                event_data.setdefault('cid', self.cid)
                event = event_mapping[event_type](sid=self.parent_plugin.sid, **event_data)

                await self.up_pending_event.put(event)
        except CancelledError:
            await self.close()
            if self.blocker is not None:
                await self.blocker.wait()
            raise

    async def send(self, websocket: Websocket):
        self.add_processor()
        while True:
            event: DownEvent = await self.down_pending_event.get()
            if isinstance(event, DisconnectEvent):
                await self.blocker.wait()
                return
            if isinstance(event, DownEvent) and is_dataclass(event):
                await websocket.send_json(asdict(event))


class PluginService:
    _inited = False
    storage_path = pathlib.Path('./services.dat')
    services: dict[uuid.UUID, Self] = {}
    max_pending_size = 50

    def __new__(cls, sid: uuid.UUID = None, _sid: uuid.UUID = None, name: str = None,
                handlers: list[Handler] = None, _inited=False):
        if not sid and _sid:
            sid = _sid
        if _inited:
            obj = object.__new__(cls)
            obj._inited = True
            return obj
        if sid and sid in cls.services:
            obj = cls.services[sid]
            obj._inited = True
            return obj
        for sid in cls.services:
            if cls.services[sid].name == name:
                obj = cls.services[sid]
                obj._inited = True
                return obj
        import inspect
        frame = inspect.currentframe()
        if frame and frame.f_back.f_code.co_filename == frame.f_code.co_filename:
            obj = object.__new__(cls)
            return obj
        else:
            raise KeyError("Cannot find PluginService for this plugin")

    def add_client(self, cid: uuid.UUID = None, client_info: ClientInfo = None, queue_max=50):
        if not cid:
            cid = uuid.uuid4()
        self.clients[cid] = ServiceClient(cid, self, client_info, queue_max)
        return self.clients[cid]

    def __init__(self, sid: uuid.UUID, name: str = None, handlers: list[Handler] = None):
        if not sid:
            raise TypeError(f'Invalid {self.__class__}')
        if self._inited:
            return
        self._inited = True
        self._sid = sid
        self.create_date = datetime.datetime.utcnow()
        self.name = name
        self.plugin_info = PluginInfo(self.sid, self.name)
        if not handlers:
            handlers = [FileReportHandler()]
        self.handlers: list[Handler] = handlers
        self.clients: dict[uuid.UUID, ServiceClient] = {}
        self.__class__.services[sid] = self

    def add_handler(self, handler: Handler):
        self.handlers.append(handler)

    # noinspection PyTypeChecker
    async def raise_event(self, event: UpEvent):
        tasks = []

        for handler in self.handlers:
            if event.type == handler.type:
                tasks.append(asyncio.create_task(handler.emit(event)))
            elif handler.type == 'default':
                tasks.append(asyncio.create_task(handler.emit(event)))

        await asyncio.gather(*tasks)

    async def broadcast(self, message: str, **kwargs):
        for cid in self.clients:
            await self.clients[cid].down_pending_event.put(BroadcastEvent(
                message=message,
                **kwargs
            ))

    @property
    def sid(self):
        return self._sid

    def __eq__(self, other):
        if isinstance(other, PluginService):
            return self.sid == other.sid and self.name == other.name
        return False

    def __hash__(self):
        return hash(self._sid)

    def __repr__(self):
        return f"<PluginService {self.name}({self.sid})>"

    @classmethod
    def load(cls):
        if not cls.storage_path.is_file():
            cls.save()
        with cls.storage_path.open('rb') as fp:
            cls.services = pickle.load(fp)
        logger.debug("Services loaded: {services}", services=cls.services)

    @classmethod
    def save(cls):
        logger.info("Saving data...")
        with cls.storage_path.open('wb') as fp:
            logger.debug("Services to save: {services}", services=cls.services)
            pickle.dump(cls.services, fp)

    @classmethod
    def register(cls, name: str, handlers=None) -> Self:
        if handlers is None:
            handlers = []

        service = PluginService(uuid.uuid4(), name, handlers=handlers)
        cls.save()
        return service

    def __getstate__(self):
        instance_dict = copy.copy(self.__dict__)
        instance_dict['clients'] = {}
        return instance_dict

    def __setstate__(self, state: dict[str, Any]):
        for key in state:
            self.__dict__[key] = state[key]
        return state


if not PluginService.services:
    PluginService.load()
