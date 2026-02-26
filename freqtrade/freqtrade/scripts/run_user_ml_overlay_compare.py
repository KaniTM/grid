from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType

SCRIPT_FILE = Path(__file__).resolve().parents[2] / "scripts" / "run-user-ml-overlay-compare.py"
MODULE_NAME = "freqtrade.scripts._run_user_ml_overlay_compare_impl"


def _load_impl() -> ModuleType:
    spec = importlib.util.spec_from_file_location(MODULE_NAME, SCRIPT_FILE)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load {SCRIPT_FILE}")

    module = importlib.util.module_from_spec(spec)
    script_dir = str(SCRIPT_FILE.parent)
    inserted = False
    if script_dir not in sys.path:
        sys.path.insert(0, script_dir)
        inserted = True

    sys.modules[MODULE_NAME] = module
    try:
        spec.loader.exec_module(module)
    finally:
        if inserted and script_dir in sys.path:
            sys.path.remove(script_dir)

    return module


_IMPL = _load_impl()

__all__ = ["build_parser", "main"]

build_parser = getattr(_IMPL, "build_parser")
main = getattr(_IMPL, "main")
