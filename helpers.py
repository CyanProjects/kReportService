import functools
import uuid
from http import HTTPStatus
from typing import Optional, Any

from quart import json, Response
from werkzeug.routing import BaseConverter, ValidationError, Map

from service.manager import PluginService
from service.structures import LocateType


class ResponseHelper:
    @classmethod
    @functools.cache
    def gen_default(cls):
        return {
            'code': 200,
            'msg': None,
            'data': None
        }

    @classmethod
    def gen_json_str(cls, dictionary: dict):
        template_dict = cls.gen_default()
        template_dict.update(dictionary)
        return json.dumps(template_dict, ensure_ascii=False)

    @classmethod
    def gen_json_response(cls, dictionary: dict, _status: HTTPStatus = HTTPStatus.OK):
        if _status == HTTPStatus.NO_CONTENT:
            return Response(status=_status)
        return Response(cls.gen_json_str(dictionary), status=_status)

    @classmethod
    def gen_kw_json_response(cls, _status: HTTPStatus = HTTPStatus.OK, **kwargs):
        return cls.gen_json_response(kwargs, _status=_status)

    gen_kw = gen_kw_json_response


class LocatePluginTypeConvertor(BaseConverter):
    def to_python(self, value: str) -> LocateType:
        return LocateType[value]

    def to_url(self, value: LocateType) -> str:
        return str(value)


class LocatePluginConvertor(BaseConverter):
    regex = (
        r"(sid\/([A-Fa-f0-9]{8}-[A-Fa-f0-9]{4}-[A-Fa-f0-9]{4}-[A-Fa-f0-9]{4}-[A-Fa-f0-9]{12}))|"
        r"(name\/[a-zA-Z][a-zA-Z0-9\-]{0,30})"
    )

    def __init__(self, map: Map, *args: Any, **kwargs: Any):
        super().__init__(map)

    def to_python(self, value: str) -> PluginService:
        sid: Optional[uuid.UUID] = None
        name: Optional[str] = None
        if value.startswith("sid/"):
            sid = uuid.UUID(value.removeprefix('sid/'))
        elif value.startswith('name/'):
            name = str(value.removeprefix('name/'))
        else:
            raise ValidationError()
        return PluginService(sid, name)

    def to_url(self, value: PluginService) -> str:
        if isinstance(value, uuid.UUID):
            return f'sid/{value}'
        elif isinstance(value, str):
            return f'name/{value}'
        raise ValidationError()