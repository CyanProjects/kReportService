import pathlib
from http import HTTPStatus

from patch_old import placeholder

from quart import Quart
from service.manager import PluginService
from helpers import LocatePluginTypeConvertor, LocatePluginConvertor, internal_error_handler

placeholder()


def create_app():
    app = Quart(__name__, instance_path=str(pathlib.Path('./instance').absolute()))
    app.config.from_prefixed_env()
    app.after_serving(PluginService.save)
    # noinspection SpellCheckingInspection
    app.url_map.converters['ltype'] = LocatePluginTypeConvertor
    app.url_map.converters['plugin'] = LocatePluginConvertor
    app.register_error_handler(HTTPStatus.INTERNAL_SERVER_ERROR, internal_error_handler)
    return app
