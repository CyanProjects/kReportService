from quart import Blueprint, request, render_template
from .structures import *
from .funcs import login_required
from .oauth import oauth

Bp = Blueprint('http:auth', __name__, url_prefix='/auth')


@Bp.route('/authorize', methods=['GET', 'POST'])
@login_required
@oauth.authorize_handler
async def authorize(*args, **kwargs):
    if request.method == 'GET':
        client_id = kwargs.get('client_id')
        client: Optional[Client] = None
        for c in OAuthStorage.clients.values():
            if c.client_id == client_id:
                client = c
                break
        kwargs['client'] = client
        return await render_template('oauthorize.html', **kwargs)

    confirm = (await request.form).get('confirm', 'no')
    return confirm == 'yes'

@Bp.route('/login', methods=['GET'])
async def login():
    return await render_template('login.html')

