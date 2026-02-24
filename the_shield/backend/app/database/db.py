import json
import os
import threading
from pathlib import Path
from typing import Any

DB_LOCK = threading.Lock()
DB_PATH = Path(os.getenv("SHIELD_DB_PATH", Path(__file__).resolve().parent / "shield_store.json"))
DEFAULT_DATA = {
    "users": [],
    "sessions": [],
    "meetings": [],
}


def _ensure_db() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    if not DB_PATH.exists():
        DB_PATH.write_text(json.dumps(DEFAULT_DATA, indent=2), encoding="utf-8")


def load_db() -> dict[str, Any]:
    _ensure_db()
    with DB_LOCK:
        raw = DB_PATH.read_text(encoding="utf-8")
        data = json.loads(raw)
    for key, default_value in DEFAULT_DATA.items():
        data.setdefault(key, list(default_value) if isinstance(default_value, list) else default_value)
    return data


def save_db(data: dict[str, Any]) -> None:
    with DB_LOCK:
        DB_PATH.write_text(json.dumps(data, indent=2), encoding="utf-8")
