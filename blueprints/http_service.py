import datetime
import uuid
from http import HTTPStatus
from json import JSONDecodeError
from itsdangerous.serializer import Serializer

from quart import Blueprint, request
from quart import json

from service.manager import PluginService
from service.structures import ReportEvent, JavascriptError, ReportLevel, UpEventType
from helpers import ResponseHelper

Bp = Blueprint('http:service', __name__, url_prefix='/api')

s1 = Serializer('secret', 'access_tok', serializer=json)


@Bp.route('/auth/<plugin:plugin>')
async def auth(plugin: PluginService):
    response = ResponseHelper.Response('OK')
    old_access = request.cookies.get('access_token', None)
    if old_access:
        tokens: list = s1.loads(old_access)
        tokens.append(plugin.sid)
        response.set_cookie('access_token', s1.dumps(tokens))
    else:
        response.set_cookie('access_token', s1.dumps([plugin.sid]))
    return response


@Bp.route('/report/<plugin:plugin>', methods=['POST'])
async def send_report(plugin: PluginService):
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
        if not (isinstance(error, dict) or (info or error)):
            raise TypeError
    except (JSONDecodeError, TypeError):
        return ResponseHelper.gen_kw(code=400, msg="'error' must be json serializable", _status=HTTPStatus.BAD_REQUEST)

    if not ((level or timestamp or description) and (info or error)):
        return ResponseHelper.gen_kw(code=400, msg="Missing required params", _status=HTTPStatus.BAD_REQUEST)

    await plugin.raise_event(ReportEvent(
        cid=cid,
        sid=plugin.sid,
        level=level, timestamp=timestamp, description=description,
        info=info, error=JavascriptError(**error) if error else None, log=log
    ))

    return ResponseHelper.gen_kw(msg='Report successfully')


@Bp.route('/report/<plugin:plugin>', methods=['GET'])
async def get_report(plugin: PluginService):
    access_cookie = request.cookies.get('access_token', [])
    tokens = s1.loads(access_cookie)
    if str(plugin.sid) not in tokens:
        return ResponseHelper.gen_kw(code=400, msg='unauthorized access', _status=HTTPStatus.UNAUTHORIZED)
    report_events = []
    for event in plugin.events:
        if event.type == UpEventType.report:
            report_events.append(event)

    return ResponseHelper.gen_kw(data=report_events)


@Bp.route('/plugin/name/<string:name>', methods=['PUT', 'POST'])
async def register_with_name(name: str):
    return ResponseHelper.gen_kw(data=str(PluginService.register_with_name(name).sid))


@Bp.route('/plugin/<plugin:plugin>', methods=['GET'])
async def fetch(plugin: PluginService):
    return ResponseHelper.gen_kw(data=plugin.plugin_info)


@Bp.route('/broadcast/<plugin:plugin>', methods=['POST'])
async def broadcast(plugin: PluginService):
    await plugin.broadcast(str(request.args.get('message', None)))
    return ResponseHelper.gen_kw(_status=HTTPStatus.NO_CONTENT)


@Bp.route('/_save', methods=['POST'])
async def save():
    PluginService.save()
    return ResponseHelper.gen_kw(_status=HTTPStatus.OK)
