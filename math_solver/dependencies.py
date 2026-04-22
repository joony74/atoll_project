from __future__ import annotations

import importlib
import platform
import sys
from pathlib import Path
from typing import Any


def _is_importable(module_name: str) -> bool:
    try:
        importlib.import_module(module_name)
        return True
    except Exception:
        return False


SYMPY_AVAILABLE = _is_importable("sympy")


def get_dependency_report(data_dir: str | Path | None = None, settings_path: str | Path | None = None) -> dict[str, Any]:
    data_path = Path(data_dir) if data_dir else None
    settings = Path(settings_path) if settings_path else None
    return {
        "python_version": sys.version.split()[0],
        "platform": platform.platform(),
        "sympy_available": SYMPY_AVAILABLE,
        "data_dir_writable": bool(data_path and data_path.exists() and data_path.is_dir()),
        "settings_exists": bool(settings and settings.exists()),
    }
