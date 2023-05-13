import asyncio
import datetime
import pickle
import uuid
from typing import Self
from quart import Websocket

from dataclasses import asdict

from .structures import Handler, MessageEvent, EventType, DataEvent


class PluginService:
    _inited = False
    services: dict[uuid.UUID, Self] = {}

    def __new__(cls, name: str = None, report_handlers: list[Handler] = None, sid: uuid.UUID = None):
        if sid and sid in cls.services:
            obj = cls.services[sid]
            obj._inited = True
            return obj
        for sid in cls.services:
            if cls.services[sid].name == name:
                obj = cls.services[sid]
                obj._inited = True
                return obj
        obj = object.__new__(cls)
        return obj

    def __init__(self, name: str, report_handlers: list[Handler] = None, sid: uuid.UUID = None):
        if not (name or sid):
            raise TypeError(f'Invalid {self.__class__}')
        if self._inited:
            return

        self._inited = True
        if sid is None:
            sid = uuid.uuid4()
        self._sid = sid
        self.create_date = datetime.datetime.utcnow()
        self.name = name
        if report_handlers:
            report_handlers = []
        self.report_handlers = report_handlers
        self.websockets: list[Websocket] = []
        self.__class__.services[sid] = self

    async def receive(self, websocket: Websocket):
        self.websockets.append(websocket)
        await websocket.send_json(asdict(
            DataEvent(
                type=EventType.message,
                data={
                    "sid": str(self.sid),
                    "name": str(self.name),
                    "created": str(self.create_date)
                }
            )
        ))

    async def broadcast(self, message: str, **kwargs):
        raise NotImplementedError("broadcast is not implemented!")

    @property
    def sid(self):
        return self._sid

    def __eq__(self, other):
        if issubclass(other, PluginService):
            return self.sid == other.sid and self.name == other.name
        return False

    def __hash__(self):
        return hash(self._sid)

    @classmethod
    def load(cls):
        with open('services.json', 'rb') as fp:
            cls.services = pickle.load(fp)

    @classmethod
    def save(cls):
        with open('services.json', 'wb') as fp:
            pickle.dump(cls.services, fp)
