from authlib.oauth2 import OAuth2Error
from quart import Blueprint, request, render_template, redirect, g, url_for
from quart.globals import request_ctx
from .structures import *
from .funcs import login_required
from .oauth import authorization, current_user

Bp = Blueprint('http:auth', __name__, url_prefix='/auth')


@Bp.route('/login', methods=['GET'])
async def login():
    if g.user is None:
        return await render_template('login.html')
    else:
        return redirect(request.args.get('next', request.referrer))


@Bp.route('/test_auth', methods=['GET'])
@login_required
async def test():
    return g.user.__dict__


@Bp.route('/auth', methods=['POST'])
async def auth():
    client = request_ctx.app.test_client()
    await client.open(
        url_for('http:oauth.auth'),
        form=await request.form,
        method=request.method,
        headers=request.headers,
        scheme=request.scheme,
        root_path=request.root_path,
        http_version=request.http_version
    )

    response = redirect(request.referrer)

    for cookie in client.cookie_jar:
        response.set_cookie(cookie.name, cookie.value, expires=cookie.expires, path=cookie.path, domain=cookie.domain,
                            secure=cookie.secure)
    return response
