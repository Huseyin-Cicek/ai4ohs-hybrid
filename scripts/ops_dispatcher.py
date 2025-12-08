"""
Ops Dispatcher
--------------
Çeşitli bakım/operasyon scriptlerini tek yerden çağırmak için kancalar sağlar.
Ağır işlemler yalnızca ilgili fonksiyon çağrıldığında çalışır (lazy import).
"""

from importlib import import_module
from typing import Any


def run_zeus_runtime(*args: Any, **kwargs: Any):
    mod = import_module("scripts.dev.zeus_runtime")
    if hasattr(mod, "main"):
        return mod.main(*args, **kwargs)
    return mod


def run_zeus_recovery(*args: Any, **kwargs: Any):
    mod = import_module("scripts.dev.zeus_recovery")
    if hasattr(mod, "main"):
        return mod.main(*args, **kwargs)
    return mod


def run_health_check(*args: Any, **kwargs: Any):
    mod = import_module("scripts.prod.health_check")
    if hasattr(mod, "main"):
        return mod.main(*args, **kwargs)
    return mod


def run_workspace_sanitizer(*args: Any, **kwargs: Any):
    mod = import_module("scripts.dev.reorg_sanitizer")
    return mod


def run_refactor_prompt_templates(*args: Any, **kwargs: Any):
    mod = import_module("src.agentic.auto_refactor.prompt_templates")
    return mod


__all__ = [
    "run_zeus_runtime",
    "run_zeus_recovery",
    "run_health_check",
    "run_workspace_sanitizer",
    "run_refactor_prompt_templates",
]
