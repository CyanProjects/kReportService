import pathlib

from quart import Quart
from service.manager import PluginService


def create_app():
    app = Quart(__name__, instance_path=str(pathlib.Path('./instance').absolute()))
    app.config.from_prefixed_env()
    app.after_serving(PluginService.save)
    return app
