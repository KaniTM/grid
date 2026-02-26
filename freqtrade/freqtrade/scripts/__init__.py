"""Expose the checked-out `scripts/` folder under `freqtrade.scripts`."""

from __future__ import annotations

from pathlib import Path

__path__ = __import__("pkgutil").extend_path(__path__, __name__)

ROOT_DIR = Path(__file__).resolve().parents[2]
SCRIPTS_DIR = ROOT_DIR / "scripts"
if SCRIPTS_DIR.is_dir():
    __path__.append(str(SCRIPTS_DIR))
