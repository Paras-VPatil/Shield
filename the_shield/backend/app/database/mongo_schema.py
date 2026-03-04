USER_SCHEMA = {
    "bsonType": "object",
    "required": ["id", "username", "password_salt", "password_hash", "created_at"],
    "additionalProperties": False,
    "properties": {
        "id": {"bsonType": "string", "description": "Application-level UUID for user."},
        "username": {"bsonType": "string", "minLength": 3, "maxLength": 50},
        "password_salt": {"bsonType": "string"},
        "password_hash": {"bsonType": "string"},
        "created_at": {"bsonType": ["string", "date"]},
    },
}

SESSION_SCHEMA = {
    "bsonType": "object",
    "required": ["token", "user_id", "created_at"],
    "additionalProperties": False,
    "properties": {
        "token": {"bsonType": "string"},
        "user_id": {"bsonType": "string"},
        "created_at": {"bsonType": ["string", "date"]},
        "expires_at": {"bsonType": ["string", "date"]},
    },
}

MEETING_SCHEMA = {
    "bsonType": "object",
    "required": ["id", "title", "owner_id", "created_at", "updated_at"],
    "additionalProperties": False,
    "properties": {
        "id": {"bsonType": "string"},
        "title": {"bsonType": "string", "minLength": 3, "maxLength": 200},
        "owner_id": {"bsonType": "string"},
        "created_at": {"bsonType": ["string", "date"]},
        "updated_at": {"bsonType": ["string", "date"]},
        "domains": {"bsonType": "array", "items": {"bsonType": "string"}},
        "open_questions": {"bsonType": "array", "items": {"bsonType": "string"}},
        "resolved_questions": {"bsonType": "array", "items": {"bsonType": "string"}},
        "minutes": {
            "bsonType": "array",
            "items": {
                "bsonType": "object",
                "required": ["id", "source", "text", "created_at"],
                "additionalProperties": False,
                "properties": {
                    "id": {"bsonType": "string"},
                    "source": {"enum": ["text", "pdf"]},
                    "filename": {"bsonType": "string"},
                    "text": {"bsonType": "string"},
                    "created_at": {"bsonType": ["string", "date"]},
                },
            },
        },
        "speaker_notes": {
            "bsonType": "array",
            "items": {
                "bsonType": "object",
                "required": ["id", "speaker", "text", "created_at"],
                "additionalProperties": False,
                "properties": {
                    "id": {"bsonType": "string"},
                    "speaker": {"bsonType": "string"},
                    "text": {"bsonType": "string"},
                    "created_at": {"bsonType": ["string", "date"]},
                },
            },
        },
        "analysis_history": {
            "bsonType": "array",
            "items": {
                "bsonType": "object",
                "required": ["id", "created_at", "input_text", "analysis"],
                "additionalProperties": False,
                "properties": {
                    "id": {"bsonType": "string"},
                    "created_at": {"bsonType": ["string", "date"]},
                    "input_text": {"bsonType": "string"},
                    "analysis": {
                        "bsonType": "object",
                        "required": [
                            "status",
                            "message",
                            "domains",
                            "questions",
                            "resolved_now",
                            "open_after_analysis",
                        ],
                        "additionalProperties": False,
                        "properties": {
                            "status": {"bsonType": "string"},
                            "message": {"bsonType": "string"},
                            "domains": {"bsonType": "array", "items": {"bsonType": "string"}},
                            "questions": {"bsonType": "array", "items": {"bsonType": "string"}},
                            "resolved_now": {"bsonType": "array", "items": {"bsonType": "string"}},
                            "open_after_analysis": {
                                "bsonType": "array",
                                "items": {"bsonType": "string"},
                            },
                        },
                    },
                },
            },
        },
    },
}

COLLECTION_SCHEMAS = {
    "users": USER_SCHEMA,
    "sessions": SESSION_SCHEMA,
    "meetings": MEETING_SCHEMA,
}

COLLECTION_INDEXES = {
    "users": [
        {"keys": [("id", 1)], "name": "uniq_users_id", "unique": True},
        {"keys": [("username", 1)], "name": "uniq_users_username", "unique": True},
        {"keys": [("created_at", -1)], "name": "idx_users_created_at_desc"},
    ],
    "sessions": [
        {"keys": [("token", 1)], "name": "uniq_sessions_token", "unique": True},
        {"keys": [("user_id", 1), ("created_at", -1)], "name": "idx_sessions_user_created_desc"},
        {
            "keys": [("expires_at", 1)],
            "name": "ttl_sessions_expires_at",
            "expireAfterSeconds": 0,
            "partialFilterExpression": {"expires_at": {"$exists": True}},
        },
    ],
    "meetings": [
        {"keys": [("id", 1)], "name": "uniq_meetings_id", "unique": True},
        {"keys": [("owner_id", 1), ("updated_at", -1)], "name": "idx_meetings_owner_updated_desc"},
        {"keys": [("owner_id", 1), ("title", 1)], "name": "idx_meetings_owner_title"},
    ],
}
