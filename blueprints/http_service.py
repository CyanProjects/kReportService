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
        if data:
            data_json = json.loads(data.decode())
        else:
            data_json = request.args
    except JSONDecodeError:
        return ResponseHelper.gen_kw(code=400, msg='Invalid data.', _status=HTTPStatus.BAD_REQUEST)
    cid = data_json.get('cid', uuid.uuid4())
    level = ReportLevel[data_json.get('level')]
    timestamp = data_json.get('timestamp', datetime.datetime.utcnow())
    description = data_json.get('description')
    info = data_json.get('info')
    error = data_json.get('error')
    log = data_json.get('log')

    try:
        if isinstance(error, str):
            error = json.loads(error)
        if not isinstance(error, dict) or error is None:
            raise TypeError
    except (JSONDecodeError, TypeError):
        return ResponseHelper.gen_kw(code=400, msg="'error' must be json serializable", _status=HTTPStatus.BAD_REQUEST)

    if not (level or timestamp or description) or not (info or error):
        return ResponseHelper.gen_kw(code=400, msg="Missing required params", _status=HTTPStatus.BAD_REQUEST)

    try:
        await PluginService(sid).raise_event(ReportEvent(
            cid=cid,
            sid=sid,
            level=level, timestamp=timestamp, description=description,
            info=info, error=JavascriptError(**error), log=log
        ))
    except KeyError as e:
        return ResponseHelper.gen_kw(code=400, msg=str(e), _status=HTTPStatus.BAD_REQUEST)

    return ResponseHelper.gen_kw(msg='Report successfully')


@Bp.route('/register/<name>', methods=['POST'])
async def register(name: str):
    return ResponseHelper.gen_kw(data=str(PluginService.register(name).sid))


@Bp.route('/broadcast/<uuid:sid>', methods=['POST'])
async def broadcast(sid: uuid.UUID):
    await PluginService(sid=sid).broadcast('test')
    return ResponseHelper.gen_kw(_status=HTTPStatus.ACCEPTED)


@Bp.route('/_save', methods=['POST'])
async def save():
    PluginService.save()
    return ResponseHelper.gen_kw(msg='pending', _status=HTTPStatus.CREATED)
