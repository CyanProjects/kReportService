class BasePluginError(Exception):
    pass


class PluginNotFoundError(BasePluginError, KeyError):
    pass


class InvalidPluginError(BasePluginError, TypeError):
    pass
