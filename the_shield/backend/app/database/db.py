import json
import os
import threading
from pathlib import Path
from typing import Any

try:
    from pymongo import MongoClient
except ImportError:  # pragma: no cover - optional for json mode
    MongoClient = None  # type: ignore[assignment]

DB_LOCK = threading.Lock()
DB_PATH = Path(os.getenv("SHIELD_DB_PATH", Path(__file__).resolve().parent / "shield_store.json"))
DB_MODE = os.getenv("SHIELD_DB_MODE", "json").strip().lower()
MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://127.0.0.1:27017")
MONGODB_DB_NAME = os.getenv("MONGODB_DB_NAME", "the_shield")
DEFAULT_DATA = {
    "users": [],
    "sessions": [],
    "meetings": [],
}
_MONGO_CLIENT: MongoClient | None = None  # type: ignore[type-arg]


def _ensure_db() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    if not DB_PATH.exists():
        DB_PATH.write_text(json.dumps(DEFAULT_DATA, indent=2), encoding="utf-8")


def _get_mongo_db():
    if MongoClient is None:
        raise RuntimeError(
            "MongoDB mode requires pymongo. Install dependencies with 'pip install -r requirements.txt'."
        )

    global _MONGO_CLIENT
    if _MONGO_CLIENT is None:
        _MONGO_CLIENT = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=5000)
    return _MONGO_CLIENT[MONGODB_DB_NAME]


def _load_from_mongo() -> dict[str, Any]:
    mongo_db = _get_mongo_db()
    data: dict[str, Any] = {}
    for collection in DEFAULT_DATA:
        data[collection] = list(mongo_db[collection].find({}, {"_id": 0}))
    return data


def _save_to_mongo(data: dict[str, Any]) -> None:
    mongo_db = _get_mongo_db()
    for collection in DEFAULT_DATA:
        docs = data.get(collection, [])
        coll = mongo_db[collection]
        coll.delete_many({})
        if docs:
            coll.insert_many(docs, ordered=False)


def load_db() -> dict[str, Any]:
    with DB_LOCK:
        if DB_MODE == "mongodb":
            data = _load_from_mongo()
        else:
            _ensure_db()
            raw = DB_PATH.read_text(encoding="utf-8")
            data = json.loads(raw)
    for key, default_value in DEFAULT_DATA.items():
        data.setdefault(key, list(default_value) if isinstance(default_value, list) else default_value)
    return data


def save_db(data: dict[str, Any]) -> None:
    with DB_LOCK:
        if DB_MODE == "mongodb":
            _save_to_mongo(data)
        else:
            DB_PATH.write_text(json.dumps(data, indent=2), encoding="utf-8")
