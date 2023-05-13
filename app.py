import pathlib

import ever_loguru
from quart import Quart

from blueprints.legacy import Bp as LegacyAPI
from blueprints.ws_status import Bp as ServiceWS

ever_loguru.install_handlers()

app = Quart(__name__, instance_path=str(pathlib.Path('./instance').absolute()))

app.register_blueprint(LegacyAPI)
app.register_blueprint(ServiceWS)

if __name__ == '__main__':
    app.run('0.0.0.0', 9800, True)
