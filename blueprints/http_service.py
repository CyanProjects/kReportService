from quart import Blueprint, request

Bp = Blueprint('http:service', __name__, url_prefix='/api')


@Bp.route('/report')
async def report():
    ...
