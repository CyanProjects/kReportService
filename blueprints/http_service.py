import datetime
import uuid
from http import HTTPStatus
from json import JSONDecodeError

from quart import Blueprint, request
from quart import json

from service.manager import PluginService
from service.structures import ReportEvent, JavascriptError, ResponseHelper, ReportLevel

Bp = Blueprint('http:service', __name__, url_prefix='/api')


@Bp.route('/report/<uuid:sid>', methods=['POST'])
async def report(sid: uuid.UUID):
    data = await request.data
    try:
        data_json = json.loads(data.decode())
    except JSONDecodeError:
        return ResponseHelper.gen_kw(code=400, msg='Invalid data.', _status=HTTPStatus.BAD_REQUEST)
    level = ReportLevel[data_json.get('level')]
    timestamp = data_json.get('timestamp', datetime.datetime.utcnow())
    description = data_json.get('description')
    info = data_json.get('info')
    error = data_json.get('error')
    log = data_json.get('log')

    if not isinstance(error, dict) or error is None:
        return ResponseHelper.gen_kw(code=400, msg="'error' must be json serializable", _status=HTTPStatus.BAD_REQUEST)

    if not (level or timestamp or description) or not (info or error):
        return ResponseHelper.gen_kw(code=400, msg="Missing required params", _status=HTTPStatus.BAD_REQUEST)

    try:
        await PluginService(sid).raise_event(ReportEvent(
            sid=sid,
            level=level, timestamp=timestamp, description=description,
            info=info, error=JavascriptError(**error), log=log
        ))
    except KeyError as e:
        return ResponseHelper.gen_kw(code=400, msg=str(e), _status=HTTPStatus.BAD_REQUEST)

    return ResponseHelper.gen_kw(msg='Report successfully')


@Bp.route('/register/<name>', methods=['PUT', 'POST'])
async def register(name: str):
    return str(PluginService.register(name).sid)


@Bp.route('/broadcast/<uuid:sid>', methods=['POST'])
async def broadcast(sid: uuid.UUID):
    await PluginService(sid=sid).broadcast('test')
    return ResponseHelper.gen_kw(_status=HTTPStatus.ACCEPTED)


@Bp.route('/_save', methods=['POST'])
async def save():
    PluginService.save()
    return ResponseHelper.gen_kw(msg='pending', _status=HTTPStatus.CREATED)
