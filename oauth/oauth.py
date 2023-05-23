import uuid
from datetime import datetime, timedelta
from typing import Optional

from quart import Quart, g, session
from oauth.structures import OAuthStorage, Client, Token, User
from authlib.integrations.flask_oauth2 import AuthorizationServer


def current_user():
    if 'id' in session:
        uid = session['id']
        return OAuthStorage.users[uuid.UUID(uid)]
    return None


def query_client(client_id: uuid.UUID | str | int):
    return OAuthStorage.clients.pop()


def save_token(token_data, request):
    token = Token(
        client=request.client,
        **token_data
    )
    token.add()
    OAuthStorage.save()


authorization = AuthorizationServer(
    query_client=query_client, save_token=save_token
)


def init_oauth(app: Quart):
    authorization.init_app(app)

    from oauth.auth_bp import Bp as AuthBlueprint
    from oauth.oauth_api_bp import Bp as OAuthAPIBlueprint

    app.register_blueprint(AuthBlueprint)
    app.register_blueprint(OAuthAPIBlueprint)

    app.before_serving(OAuthStorage.load)
    app.after_serving(OAuthStorage.save)

    @app.before_request
    async def set_user():
        g.user = current_user()

    return app
