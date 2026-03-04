import os
import sys

from pymongo import MongoClient
from pymongo.errors import OperationFailure

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from app.database.mongo_schema import COLLECTION_INDEXES, COLLECTION_SCHEMAS


def ensure_collection_schema(db, name: str, json_schema: dict) -> None:
    validator = {"$jsonSchema": json_schema}
    if name in db.list_collection_names():
        db.command(
            {
                "collMod": name,
                "validator": validator,
                "validationLevel": "moderate",
                "validationAction": "error",
            }
        )
        print(f"[OK] Updated validator: {name}")
        return

    db.create_collection(
        name,
        validator=validator,
        validationLevel="moderate",
        validationAction="error",
    )
    print(f"[OK] Created collection with validator: {name}")


def ensure_indexes(db, name: str, indexes: list[dict]) -> None:
    coll = db[name]
    for index in indexes:
        options = {k: v for k, v in index.items() if k != "keys"}
        created = coll.create_index(index["keys"], **options)
        print(f"[OK] Ensured index on {name}: {created}")


def main() -> None:
    mongo_uri = os.getenv("MONGODB_URI", "mongodb://127.0.0.1:27017")
    db_name = os.getenv("MONGODB_DB_NAME", "the_shield")

    client = MongoClient(mongo_uri, serverSelectionTimeoutMS=5000)
    db = client[db_name]

    try:
        client.admin.command("ping")
    except Exception as exc:
        raise SystemExit(f"[ERROR] Could not connect to MongoDB: {exc}") from exc

    print(f"[INFO] Connected to MongoDB. Database: {db_name}")

    for collection_name, schema in COLLECTION_SCHEMAS.items():
        try:
            ensure_collection_schema(db, collection_name, schema)
        except OperationFailure as exc:
            raise SystemExit(
                f"[ERROR] Failed applying validator for '{collection_name}': {exc.details or exc}"
            ) from exc

    for collection_name, indexes in COLLECTION_INDEXES.items():
        ensure_indexes(db, collection_name, indexes)

    print("[DONE] Mongo schema and indexes are ready.")


if __name__ == "__main__":
    main()
