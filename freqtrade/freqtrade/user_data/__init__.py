"""Allow importing `freqtrade.user_data` from the repo-level user_data tree."""

from __future__ import annotations

from pathlib import Path

__path__ = __import__("pkgutil").extend_path(__path__, __name__)

ROOT_DIR = Path(__file__).resolve().parents[2]
USER_DATA_DIR = ROOT_DIR / "user_data"
if USER_DATA_DIR.is_dir():
    __path__.append(str(USER_DATA_DIR))
