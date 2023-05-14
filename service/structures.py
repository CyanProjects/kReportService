import asyncio
import collections
import datetime
import enum
import typing
import uuid as uuid
from asyncio import Event
from abc import ABC, abstractmethod
from dataclasses import dataclass, KW_ONLY, field
from http import HTTPStatus
from typing import TypedDict, Optional, Literal, Any

try:
    from typing import NotRequired, Required, _AnyMeta
except ImportError:
    from typing_extensions import NotRequired, Required, _AnyMeta

typing.NotRequired, typing.Required, typing._AnyMeta = NotRequired, Required, _AnyMeta

from strongtyping.strong_typing import match_class_typing
from quart import json, Response

StrSetArrayType = list[str] | tuple[str] | set[str]


class MyStrEnum(str, enum.Enum):
    def __repr__(self):
        return self.value


if not hasattr(enum, 'StrEnum'):
    enum.StrEnum = MyStrEnum


class ValuedEvent(Event):
    def __init__(self):
        super().__init__()
        self._waiters = collections.deque()
        self._value = None

    def set_with_value(self, value: Any):
        if not self._value:
            self._value = value

            for fut in self._waiters:
                if not fut.done():
                    fut.set_result(value)

    def clear(self):
        """Reset the internal flag to false. Subsequently, coroutines calling
        wait() will block until set() is called to set the internal flag
        to true again."""
        self._value = None

    async def wait(self) -> Any:
        """Block until the internal flag is true.

        If the internal flag is true on entry, return True
        immediately.  Otherwise, block until another coroutine calls
        set() to set the flag to true, then return True.
        """
        if self._value:
            return self._value

        fut = asyncio.get_event_loop().create_future()
        self._waiters.append(fut)
        try:
            return await fut
        finally:
            self._waiters.remove(fut)


class PackageInfo(TypedDict, total=False):
    name: str
    description: str
    version: str
    main: str
    typings: str
    license: str
    scripts: StrSetArrayType
    keywords: StrSetArrayType
    peerDependencies: StrSetArrayType


class PluginInfoBasic:
    sid: Optional[uuid.UUID | str] = None
    name: Optional[str] = None

    def __init__(self):
        if not (self.name or self.sid):
            raise TypeError(f'Invalid {PluginInfoBasic}')


@dataclass
class PluginInfo(PluginInfoBasic):
    sid: Optional[uuid.UUID | str] = None
    name: Optional[str] = None
    version: Optional[str] = None
    _ = KW_ONLY
    description: Optional[str] = ''
    packageInfo: Optional[PackageInfo] = field(default_factory=PackageInfo)

    def __post_init__(self):
        if not isinstance(self.sid, uuid.UUID) and self.sid is not None:
            self.sid = uuid.UUID(self.sid)


class GeneralEventType(enum.StrEnum):
    notice = 'notice'
    status = 'status'
    message = 'message'
    other = 'other'


class UpEventType(enum.StrEnum):
    # # General Event
    # notice = 'notice'
    # status = 'status'
    # message = 'message'

    # Up Events
    required = 'required'
    fetch = 'fetch'
    report = 'report'


class DownEventType(enum.StrEnum):
    # # General Event
    # notice = 'notice'
    # status = 'status'
    # message = 'message'

    # Down Events
    broadcast = 'broadcast'
    alert = 'alert'
    hmr = 'hmr'  # may not be able to use because of the koishi policy
    execute = 'execute'  # may not be able to use because of the koishi policy


class ReportLevel(enum.StrEnum):
    info = 'info'
    warn = 'warn'
    fails = 'fails'
    error = 'error'
    crash = 'crash'


@match_class_typing
class JavascriptError(TypedDict):
    name: str
    message: str
    stacktrace: Optional[str]


@dataclass
class BaseEvent:
    type: GeneralEventType


@dataclass
class UpEvent(BaseEvent):
    sid: uuid.UUID
    type: UpEventType | GeneralEventType


@dataclass
class DownEvent(BaseEvent):
    type: DownEventType | GeneralEventType


@dataclass
class StatusEvent(DownEvent):
    type: Literal[GeneralEventType.status] = field(init=False)
    sid: str
    name: str
    message: Optional[str] = None

    def __post_init__(self):
        self.type = GeneralEventType.status


@dataclass
class BroadcastEvent(DownEvent):
    type: Literal[DownEventType.broadcast] = field(init=False)
    message: str
    highlight: bool = False

    def __post_init__(self):
        self.type = DownEventType.broadcast


@dataclass
class DataEvent(BaseEvent):
    """
    Message Event: brings a struct in event
    :var data: the struct(dict, tuple or list) to bring
    """
    data: dict | tuple | list


@dataclass
class MessageEvent(BaseEvent):
    """
    Message Event: brings a message
    :var message: the message to bring
    """
    message: str
    type: Literal[GeneralEventType.message] = field(init=False)

    def __post_init__(self):
        self.type = GeneralEventType.message


@dataclass
class ReportEvent(UpEvent):
    type: Literal[UpEventType.report] = field(init=False)
    level: ReportLevel
    description: str
    timestamp: int | float | datetime.datetime = datetime.datetime.utcnow()
    info: Optional[str] = None
    error: Optional[JavascriptError] = None
    log: Optional[str] = None

    def __post_init__(self):
        self.type = UpEventType.report
        if not isinstance(self.timestamp, datetime.datetime):
            self.timestamp = datetime.datetime.fromtimestamp(self.timestamp, tz=datetime.UTC)


event_mapping = {
    UpEventType.report: ReportEvent,
    GeneralEventType.message: MessageEvent,
    GeneralEventType.status: StatusEvent,
    DownEventType.broadcast: BroadcastEvent,
}


class Handler(ABC):
    type = 'default'

    @abstractmethod
    async def emit(self, report: UpEvent):
        pass


class ReportHandler(Handler, ABC):
    type = UpEventType.report

    @abstractmethod
    async def emit(self, report: ReportEvent):
        pass


class NoticeHandler(Handler, ABC):
    type = GeneralEventType.notice

    @abstractmethod
    async def emit(self, report: BaseEvent):
        pass


class ResponseHelper:
    template = {
        'code': 200,
        'msg': None,
        'data': None
    }

    @classmethod
    def gen_json_str(cls, dictionary: dict):
        template_dict = cls.template
        template_dict.update(dictionary)
        return json.dumps(template_dict, ensure_ascii=False)

    @classmethod
    def gen_json_response(cls, dictionary: dict, _status: HTTPStatus = HTTPStatus.OK):
        return Response(cls.gen_json_str(dictionary), status=_status)

    @classmethod
    def gen_kw_json_response(cls, _status: HTTPStatus = HTTPStatus.OK, **kwargs):
        return cls.gen_json_response(kwargs, _status=_status)

    gen_kw = gen_kw_json_response
