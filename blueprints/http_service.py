import datetime
import uuid
from http import HTTPStatus
from json import JSONDecodeError

from quart import Blueprint, request, g
from quart import json

from oauth.funcs import login_required
from service.manager import PluginService
from service.structures import ReportEvent, JavascriptError, ReportLevel, UpEventType
from helpers import ResponseHelper

Bp = Blueprint('http:service', __name__, url_prefix='/api')


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
@login_required
async def get_report(plugin: PluginService):
    user = g.user
    if not user:
        ResponseHelper.gen_kw(code=401, _status=HTTPStatus.UNAUTHORIZED, msg='User not login')
    if plugin.sid not in user.owned_services:
        ResponseHelper.gen_kw(code=401, _status=HTTPStatus.UNAUTHORIZED, msg='User not owned this PluginService')
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
