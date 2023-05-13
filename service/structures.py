import datetime
import enum
from abc import ABC, abstractmethod
from dataclasses import dataclass, KW_ONLY, field
from typing import TypedDict, Optional

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
    description: Optional[str] = ''
    packageInfo: Optional[PackageInfo] = field(default_factory=PackageInfo)


class ReportType(enum.IntEnum):
    info = 0x0001
    warn = 0x0002
    error = 0x0010
    fails = 0x0030


@dataclass
class Report:
    type: ReportType
    timestamp: int | float | datetime.datetime
    description: str
    exception: Optional[str] = None

    def __post_init__(self):
        if not isinstance(self.timestamp, datetime.datetime):
            self.timestamp = datetime.datetime.fromtimestamp(self.timestamp)


class UpMessage(TypedDict):
    upType: str
    event: dict


class Handler(ABC):
    @abstractmethod
    async def emit(self, report: Report):
        pass
