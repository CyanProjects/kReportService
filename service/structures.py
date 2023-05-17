import datetime
import enum
import uuid as uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, KW_ONLY, field
from typing import TypedDict, Optional, Literal

from strongtyping.strong_typing import match_class_typing

StrSetArrayType = list[str] | tuple[str] | set[str]


class MyStrEnum(str, enum.Enum):
    def __repr__(self):
        return self.value


if not hasattr(enum, 'StrEnum'):
    enum.StrEnum = MyStrEnum


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


@dataclass
class PluginInfo:
    sid: Optional[uuid.UUID | str] = None
    name: Optional[str] = None

    def __post_init__(self):
        if not (self.name or self.sid):
            raise TypeError(f'Invalid {PluginInfo}')


@dataclass
class ClientInfo(PluginInfo):
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


class SpecialEventType(enum.StrEnum):
    closed = 'closed'
    disconnect = 'closed'


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
    cid: Optional[uuid.UUID]
    type: UpEventType | GeneralEventType


@dataclass
class DownEvent(BaseEvent):
    type: DownEventType | GeneralEventType


@dataclass
class SpecialEvent(DownEvent):
    type: SpecialEventType


@dataclass
class DisconnectEvent(SpecialEvent):
    type: Literal[SpecialEventType.disconnect] = field(init=False)

    def __post_init__(self):
        self.type = SpecialEventType.disconnect


@dataclass
class StatusEvent(DownEvent):
    type: Literal[GeneralEventType.status] = field(init=False)
    sid: str
    name: str
    cid: Optional[str] = None
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
    async def emit(self, plugin: "PluginService", event: UpEvent):
        pass


class ReportHandler(Handler, ABC):
    type = UpEventType.report

    @abstractmethod
    async def emit(self, plugin: "PluginService", report: ReportEvent):
        pass


class NoticeHandler(Handler, ABC):
    type = GeneralEventType.notice

    @abstractmethod
    async def emit(self, plugin: "PluginService", event: BaseEvent):
        pass


class LocateType(enum.StrEnum):
    sid = 'sid'
    name = 'name'
