import pathlib

from patch_old import placeholder

from quart import Quart
from service.manager import PluginService
from helpers import LocatePluginTypeConvertor, LocatePluginConvertor

placeholder()


def create_app():
    app = Quart(__name__, instance_path=str(pathlib.Path('./instance').absolute()))
    app.config.from_prefixed_env()
    app.after_serving(PluginService.save)
    # noinspection SpellCheckingInspection
    app.url_map.converters['ltype'] = LocatePluginTypeConvertor
    app.url_map.converters['plugin'] = LocatePluginConvertor
    return app
