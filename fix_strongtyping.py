import typing
import importlib

try:
    # noinspection PyProtectedMember
    from typing import NotRequired, Required, _AnyMeta
except ImportError:
    # Fix strongtyping
    # noinspection PyUnresolvedReferences,PyProtectedMember
    from typing_extensions import NotRequired, Required, _AnyMeta

# noinspection PyTypedDict
typing.NotRequired, typing.Required, typing._AnyMeta = NotRequired, Required, _AnyMeta

importlib.import_module("strongtyping.strong_typing")
