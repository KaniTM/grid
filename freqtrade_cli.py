"""Entry point bootstrap that keeps the editable repo package available."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


def _is_repo_module(module: object, package_dir: Path) -> bool:
    spec = getattr(module, "__spec__", None)
    if spec is None:
        return False
    origin = getattr(spec, "origin", None)
    if not origin:
        return False
    try:
        return Path(origin).resolve().parent == package_dir
    except OSError:
        return False


def _prime_repo_package() -> None:
    repo_root = Path(__file__).resolve().parent
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))
    package_dir = repo_root / "freqtrade"
    if str(package_dir) not in sys.path:
        sys.path.insert(0, str(package_dir))

    existing = sys.modules.get("freqtrade")
    if existing and _is_repo_module(existing, package_dir):
        return

    spec = importlib.util.spec_from_file_location(
        "freqtrade", package_dir / "__init__.py"
    )
    if spec is None or spec.loader is None:
        raise ImportError("Could not locate the freqtrade package in the repo")

    module = importlib.util.module_from_spec(spec)
    sys.modules["freqtrade"] = module
    spec.loader.exec_module(module)


_prime_repo_package()

from freqtrade.main import main as _main


def main(sysargv: list[str] | None = None) -> None:
    return _main(sysargv)
