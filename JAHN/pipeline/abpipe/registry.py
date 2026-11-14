"""Name -> module class. Built-ins register on import; external modules load as plugins."""
from __future__ import annotations

import importlib

KINDS = ("generator", "filter", "scorer", "aggregator")
_REG: dict[str, dict[str, type]] = {k: {} for k in KINDS}
_BUILTINS = ("generators", "filters", "scorers", "aggregators")
_loaded = False


def register(kind: str, name: str):
    if kind not in KINDS:
        raise ValueError(f"unknown module kind {kind!r}; expected one of {KINDS}")

    def deco(cls):
        if name in _REG[kind]:
            raise ValueError(f"{kind} {name!r} is already registered by {_REG[kind][name].__module__}")
        cls.kind, cls.name = kind, name
        _REG[kind][name] = cls
        return cls

    return deco


def load_builtin() -> None:
    global _loaded
    if not _loaded:
        _loaded = True
        for pkg in _BUILTINS:
            importlib.import_module(f"abpipe.{pkg}")


def load_plugins(modules) -> None:
    """Import external modules; importing them runs their @register decorators."""
    for m in modules or []:
        importlib.import_module(m)


def get(kind: str, name: str) -> type:
    load_builtin()
    try:
        return _REG[kind][name]
    except KeyError:
        raise KeyError(f"no {kind} named {name!r}; available: {sorted(_REG[kind])}") from None


def available() -> dict[str, list[str]]:
    load_builtin()
    return {k: sorted(v) for k, v in _REG.items()}
