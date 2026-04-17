import os
from pymongo import MongoClient
import sys

# Add path to import mongo_schema
sys.path.append(os.path.join(os.getcwd(), 'the_shield', 'backend'))
from app.database.mongo_schema import USER_SCHEMA

def debug_mongo():
    mongo_uri = os.getenv("MONGODB_URI", "mongodb://127.0.0.1:27017")
    db_name = os.getenv("MONGODB_DB_NAME", "the_shield")
    client = MongoClient(mongo_uri)
    db = client[db_name]
    
    name = 'users'
    validator = {"$jsonSchema": USER_SCHEMA}
    
    try:
        if name in db.list_collection_names():
            print(f"Collection {name} exists, attempting collMod...")
            res = db.command({
                "collMod": name,
                "validator": validator,
                "validationLevel": "moderate",
                "validationAction": "error",
            })
            print("collMod success:", res)
        else:
            print(f"Creating collection {name}...")
            db.create_collection(name, validator=validator)
            print("Creation success")
    except Exception as e:
        print("Caught exception:", type(e))
        if hasattr(e, 'details'):
            print("Details:", e.details)
        else:
            print("Exception:", e)

if __name__ == "__main__":
    debug_mongo()
