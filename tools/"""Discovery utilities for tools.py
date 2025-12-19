"""Discovery utilities for tools."""

import importlib
import pkgutil
from typing import Optional

try:
    from .base import BaseTool
except Exception:
    from tools.base import BaseTool

from .registry import register_tool


def discover_tools() -> None:
    """
    Import all tool modules and register their BaseTool subclasses.

    Attempts to import the package to obtain a usable __path__, falls back
    to the local 'tools' package name if necessary.
    """
    package_name = __package__ or "tools"
    exclude = {"base", "registry", "loader"}

    pkg = None
    pkg_path: Optional[list] = None

    try:
        pkg = importlib.import_module(package_name)
        pkg_path = getattr(pkg, "__path__", None)
    except Exception:
        pkg = None
        pkg_path = None

    if not pkg_path:
        try:
            pkg = importlib.import_module("tools")
            package_name = "tools"
            pkg_path = getattr(pkg, "__path__", None)
        except Exception:
            # Can't find a usable package path — nothing to discover
            return

    prefix = f"{package_name}."

    for module_info in pkgutil.iter_modules(pkg_path, prefix):
        module_name = module_info.name
        short_name = module_name.rsplit(".", 1)[-1]
        if short_name in exclude:
            continue

        try:
            module = importlib.import_module(module_name)
        except Exception:
            # Skip modules that fail to import
            continue

        for attr in vars(module).values():
            if not isinstance(attr, type):
                continue
            if not issubclass(attr, BaseTool) or attr is BaseTool:
                continue
            if not getattr(attr, "name", None):
                continue
            register_tool(attr)
