import typing
import importlib

try:
    # noinspection PyProtectedMember
    from typing import Self, NotRequired, Required, _AnyMeta
except ImportError:
    # Fix strongtyping
    # noinspection PyUnresolvedReferences,PyProtectedMember
    from typing_extensions import Self, NotRequired, Required, _AnyMeta

# noinspection PyTypedDict
typing.NotRequired, typing.Required, typing.Self, typing._AnyMeta = NotRequired, Required, Self, _AnyMeta

importlib.import_module("strongtyping.strong_typing")


def placeholder():
    pass
