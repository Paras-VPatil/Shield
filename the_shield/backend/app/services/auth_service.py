import hashlib
import secrets
from datetime import datetime, timezone
from typing import Optional
from uuid import uuid4

from app.database.db import load_db, save_db


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _hash_password(password: str, salt: str) -> str:
    return hashlib.sha256(f"{salt}:{password}".encode("utf-8")).hexdigest()


def register_user(username: str, password: str) -> dict:
    data = load_db()
    normalized = username.strip().lower()
    if any(user["username"] == normalized for user in data["users"]):
        raise ValueError("Username already exists.")

    salt = secrets.token_hex(8)
    user = {
        "id": str(uuid4()),
        "username": normalized,
        "password_salt": salt,
        "password_hash": _hash_password(password, salt),
        "created_at": _now_iso(),
    }
    data["users"].append(user)
    save_db(data)
    return {"id": user["id"], "username": user["username"]}


def username_exists(username: str) -> bool:
    data = load_db()
    normalized = username.strip().lower()
    return any(user["username"] == normalized for user in data["users"])


def authenticate_user(username: str, password: str) -> Optional[dict]:
    data = load_db()
    normalized = username.strip().lower()
    user = next((u for u in data["users"] if u["username"] == normalized), None)
    if not user:
        return None
    if _hash_password(password, user["password_salt"]) != user["password_hash"]:
        return None
    return {"id": user["id"], "username": user["username"]}


def create_session_token(user_id: str) -> str:
    token = secrets.token_urlsafe(32)
    data = load_db()
    data["sessions"].append(
        {
            "token": token,
            "user_id": user_id,
            "created_at": _now_iso(),
        }
    )
    save_db(data)
    return token


def get_user_by_token(token: str) -> Optional[dict]:
    data = load_db()
    session = next((entry for entry in data["sessions"] if entry["token"] == token), None)
    if not session:
        return None
    user_id = session["user_id"]
    user = next((u for u in data["users"] if u["id"] == user_id), None)
    if not user:
        return None
    return {"id": user["id"], "username": user["username"]}


def revoke_session_token(token: str) -> None:
    data = load_db()
    before = len(data["sessions"])
    data["sessions"] = [entry for entry in data["sessions"] if entry["token"] != token]
    if len(data["sessions"]) != before:
        save_db(data)
