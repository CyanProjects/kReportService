import asyncio
import copy
import datetime
import pathlib
import pickle
import uuid
from dataclasses import asdict, is_dataclass
from typing import Self, Any

from quart import Websocket, json

from log import logger
from .structures import Handler, StatusEvent, BroadcastEvent, DownEvent, event_mapping, UpEvent, ValuedEvent, \
    ReportHandler, ReportEvent


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

    def __init__(self, sid: uuid.UUID, name: str = None, handlers: list[Handler] = None):
        if not sid:
            raise TypeError(f'Invalid {self.__class__}')
        if self._inited:
            return

        self._inited = True
        self._sid = sid
        self.create_date = datetime.datetime.utcnow()
        self.name = name
        if handlers:
            handlers = [FileReportHandler()]
        self.handlers = handlers
        self.pending_event: ValuedEvent = ValuedEvent()
        self.__class__.services[sid] = self

    def add_handler(self, handler: Handler):
        self.handlers.append(handler)

    async def raise_event(self, event: UpEvent):
        tasks = []

        for handler in self.handlers:
            if event.type == handler.type:
                tasks.append(asyncio.create_task(handler.emit(event)))
            elif handler.type == 'default':
                tasks.append(asyncio.create_task(handler.emit(event)))

        await asyncio.gather(*tasks)

    async def receive(self, websocket: Websocket):
        await websocket.send_json(asdict(
            StatusEvent(
                sid=str(self.sid),
                name=str(self.name),
                message="Connected to server"
            )
        ))

        while True:
            event_data = await websocket.receive_json()
            event_type = event_data['type']
            event_data.pop('type')
            event = event_mapping[event_type](sid=self.sid, **event_data)

            await self.raise_event(event)

    async def send(self, websocket: Websocket):
        while True:
            event: DownEvent = await self.pending_event.wait()
            if isinstance(event, DownEvent) and is_dataclass(event):
                await websocket.send_json(asdict(event))

    async def broadcast(self, message: str, **kwargs):
        self.pending_event.set_with_value(BroadcastEvent(
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
    instance_dict['pending_event'] = None
    return instance_dict


def __setstate__(self, state: dict[str, Any]):
    if 'pending_event' in state:
        state['pending_event'] = ValuedEvent()
    for key in state:
        self.__dict__[key] = state[key]
    return state


if not PluginService.services:
    PluginService.load()
