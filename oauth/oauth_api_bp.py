from http import HTTPStatus
from typing import TypedDict

from authlib.oauth2 import OAuth2Error
from quart import g, Blueprint, request, render_template, redirect, url_for, session
from strongtyping.strong_typing import match_class_typing

from .structures import *
from .funcs import login_required
from .oauth import authorization, current_user

Bp = Blueprint('http:oauth', __name__, url_prefix='/api/oauth')


@match_class_typing
class LoginForm(TypedDict):
    username: str
    password: str


@Bp.route('/token', methods=['POST'])
def issue_token():
    return authorization.create_token_response()


@Bp.route('/auth', methods=['POST'])
async def auth():
    form = await request.form
    if not (form and ('username' in form and 'password' in form)):
        return 'Login Failed', HTTPStatus.BAD_REQUEST
    form: LoginForm = LoginForm(**form)
    for user in OAuthStorage.users.values():
        if user.name == form['username'] and user.check_auth(form['password']):
            session['id'] = user.user_id
            return 'Login Success', HTTPStatus.OK
    return 'Login Failed', HTTPStatus.BAD_REQUEST


@Bp.route('/create_client', methods=['GET', 'POST'])
@login_required
async def create_client():
    user = current_user()
    client = Client(
        user=user,
        redirect_uris=[request.referrer],
        scopes=['test']
    )
    client.add()
    OAuthStorage.save()

    return redirect(url_for('http:oauth.authorize'))


@Bp.route('/authorize', methods=['GET', 'POST'])
@login_required
async def authorize():
    user = current_user()
    # if user log status is not true (Auth server), then to log it in
    form = await request.form
    if request.method == 'GET':
        try:
            grant = authorization.get_consent_grant(end_user=user)
        except OAuth2Error as error:
            return error.error
        return render_template('oauthorize.html', user=user, grant=grant)
    if not user and 'username' in form:
        username = form.get('username')
        user = None
        for u in OAuthStorage.users.values():
            if u.name == username:
                user = u
                break
    if form['confirm']:
        grant_user = user
    else:
        grant_user = None
    return authorization.create_authorization_response(grant_user=grant_user)
