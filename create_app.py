import pathlib
from http import HTTPStatus

from patch_old import placeholder

from quart import Quart
from service.manager import PluginService
from helpers import LocatePluginTypeConvertor, LocatePluginConvertor, internal_error_handler
from blueprints.http_service import Bp as HTTPService
from blueprints.legacy import Bp as LegacyAPI
from blueprints.ws_status import Bp as ServiceWS

placeholder()


def create_app():
    app = Quart(__name__, instance_path=str(pathlib.Path('./instance').absolute()))
    app.config.from_prefixed_env()
    app.after_serving(PluginService.save)
    # noinspection SpellCheckingInspection
    app.url_map.converters['ltype'] = LocatePluginTypeConvertor
    app.url_map.converters['plugin'] = LocatePluginConvertor
    app.register_error_handler(HTTPStatus.INTERNAL_SERVER_ERROR, internal_error_handler)

    app.register_blueprint(LegacyAPI)
    app.register_blueprint(ServiceWS)
    app.register_blueprint(HTTPService)

    return app
