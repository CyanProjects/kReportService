# noinspection All
# noqa

from log import logger
import asyncio
import datetime
from typing import Dict

from quart import Blueprint, request, jsonify

Bp = Blueprint('legacy', __name__, url_prefix='/api/vanilla')
request_dict: Dict[str, datetime.datetime] = {}  # ip: time.time()

emailUser = {
    'username': 'report.lovemilk@hotmail.com',
    'password': 'report.koishi.email'
}

SUPPORT_TARGETS = {
    'public.zhuhansan666@outlook.com',
    'Cyan_Changes@outlook.com'
}


def send(message, ipaddr):
    filename = f'./reports/{ipaddr}-{datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S-%f")[:-3]}.log'
    logger.info("{addr} write to {fn}", addr=ipaddr, fn=filename)
    with open(filename, 'w+', encoding='u8') as f:
        f.write(message)


@Bp.route('/')
async def report_api():
    # test url
    # /api/report?senderQwq114514191810000000000000000=report.lovemilk@hotmail.com&targetEmail=public.zhuhansan666@outlook.com&msg=test&subject=subjectTest

    sender = (await request.values).get('senderQwq114514191810000000000000000')
    target = (await request.values).get('targetEmail')
    subject = (await request.values).get('subject')
    msg = (await request.values).get('msg')

    if sender != emailUser['username']:
        logger.info("Fuck you, {addr}! Your sender email wasn't supported! Don't use my API!", addr=request.remote_addr)
        return jsonify(code=114514, msg='Fuck you! Your sender email was not support! Don\'t use my API!')

    if target not in SUPPORT_TARGETS:
        logger.info('{addr} Invalid Target', addr=request.remote_addr)
        return jsonify(code=1145, msg='target error')

    if type(msg) != str or not msg:
        logger.info("{addr} Wrong or Empty Message", addr=request.remote_addr)
        return jsonify(code=1145, msg='msg error/emtpy')

    if type(subject) != str or not subject:
        logger.info("{addr} Wrong or Empty Subject", addr=request.remote_addr)
        return jsonify(code=1145, msg='subject error/emtpy')

    latest_request_time = request_dict.get(request.remote_addr)
    latest_sent_duration = (datetime.datetime.now() - latest_request_time)
    if latest_request_time is not None and latest_sent_duration < datetime.timedelta(seconds=10):
        logger.info("{addr} Request Too Fast", addr=request.remote_addr)
        return jsonify(code=1145, msg='too fast')

    for i in range(3):
        try:
            # emsg = email.message.EmailMessage()
            # emsg['Subject'] = subject
            # emsg['From'] = emailUser['username']
            # emsg['To'] = target
            # emsg.set_content(msg)
            # send(emsg)
            send(msg, request.remote_addr)
            request_dict[request.remote_addr] = datetime.datetime.now()
            logger.info('Sent successful! (target: {})', request.remote_addr)
            return jsonify(code=200, msg='success')
        except Exception as e:
            logger.info('{addr} ({}/3)send email error: {}', i + 1, e, addr=request.remote_addr)
            await asyncio.sleep(3)
    else:
        logger.info('{addr} Failed to call API! (↑send email error↑)', addr=request.remote_addr)
        return jsonify(code=1145, msg='API call failed!')
