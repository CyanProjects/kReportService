import datetime
import enum
from abc import ABC, abstractmethod
from dataclasses import dataclass, KW_ONLY, field, InitVar
from typing import TypedDict, Optional

import uuid as uuid

StrSetArrayType = list[str] | tuple[str] | set[str]


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
    name: str
    version: str
    _ = KW_ONLY
    sid: Optional[uuid.UUID | str] = None
    description: Optional[str] = ''
    packageInfo: Optional[PackageInfo] = field(default_factory=PackageInfo)

    def __post_init__(self):
        if not isinstance(self.sid, uuid.UUID) and self.sid is not None:
            self.sid = uuid.UUID(self.sid)


class EventType(enum.StrEnum):
    notice = 'notice'
    status = 'status'
    required = 'required'
    report = 'report'
    message = 'message'


class ReportLevel(enum.StrEnum):
    info = 'info'
    warn = 'warn'
    error = 'error'
    fails = 'fails'
    crash = 'crash'


class JavascriptError(TypedDict):
    name: str
    message: str
    stacktrace: Optional[str]


@dataclass
class BaseEvent:
    type: EventType


@dataclass
class MessageEvent(BaseEvent):
    """
    Message Event: brings a message
    :var message: the message to bring
    """
    message: str


@dataclass
class ReportEvent(BaseEvent):
    level: ReportLevel
    timestamp: int | float | datetime.datetime
    description: str
    info: Optional[str] = None
    error: Optional[JavascriptError] = None

    def __post_init__(self):
        if not isinstance(self.timestamp, datetime.datetime):
            self.timestamp = datetime.datetime.fromtimestamp(self.timestamp, tz=datetime.UTC)


@dataclass
class Message:
    messageType: str
    data: dict


@dataclass
class DownMessage(Message):
    pass


@dataclass
class UpMessage(Message):
    pass


class Handler(ABC):
    @abstractmethod
    async def emit(self, report: ReportEvent):
        pass
