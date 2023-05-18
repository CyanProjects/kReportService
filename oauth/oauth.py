from datetime import datetime, timedelta
from typing import Optional

from flask_oauthlib.provider import OAuth2Provider
from quart import Quart
from oauth.structures import OAuthStorage, Token, User

oauth = OAuth2Provider()


@oauth.clientgetter
def load_client(client_id: str):
    return OAuthStorage.clients[client_id]


@oauth.tokengetter
def load_token(access_token=None, refresh_token=None):
    if access_token:
        for token in OAuthStorage.tokens.values():
            if token.access_token == access_token:
                return token
    elif refresh_token:
        for token in OAuthStorage.tokens.values():
            if token.refresh_token == refresh_token:
                return token


@oauth.tokensetter
def save_token(token, request, *args, **kwargs):
    tokens = []
    for tok in OAuthStorage.tokens.values():
        if tok.client_id == request.client.client_id and tok.user_id == request.user.id:
            tok.delete()

    expires_in = token.get('expires_in')
    expires = datetime.utcnow() + timedelta(seconds=expires_in)

    tok = Token(
        access_token=token['access_token'],
        refresh_token=token['refresh_token'],
        token_type=token['token_type'],
        scopes=token['scope'],
        expires=expires,
        client=OAuthStorage.clients[request.client.client_id],
        user=OAuthStorage.users[request.user.id],
    )

    tok.add()
    OAuthStorage.save()
    return tok


@oauth.usergetter
def get_user(username, password, *args, **kwargs):
    user: Optional[User] = None
    for u in OAuthStorage.users.values():
        if u.name == username:
            user = u
            break
    if not user:
        return None
    if user.check_auth(password):
        return user
    return None


def init_oauth(app: Quart):
    oauth.init_app(app)

    from oauth.oauth_bp import Bp as OAuthBlueprint

    app.register_blueprint(OAuthBlueprint)

    return app
