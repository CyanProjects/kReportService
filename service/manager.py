import json

from structures import Handler


class PluginService:
    def __init__(self, name: str, report_handlers: list[Handler]):
        self.name = name
        self.report_handlers = report_handlers
