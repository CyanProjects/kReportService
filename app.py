import pathlib

import ever_loguru
from quart import Quart

from blueprints.legacy import Bp as LegacyAPI
from blueprints.ws_status import Bp as ServiceWS
from blueprints.http_service import Bp as HTTPService
from create_app import create_app

app = create_app()

app.register_blueprint(LegacyAPI)
app.register_blueprint(ServiceWS)
app.register_blueprint(HTTPService)

if __name__ == '__main__':
    app.run('0.0.0.0', 9800, True, use_reloader=True)
