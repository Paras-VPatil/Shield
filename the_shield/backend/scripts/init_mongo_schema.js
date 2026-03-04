const dbName = process.env.MONGODB_DB_NAME || "the_shield";
const appDb = db.getSiblingDB(dbName);

const COLLECTION_SCHEMAS = {
  users: {
    bsonType: "object",
    required: ["id", "username", "password_salt", "password_hash", "created_at"],
    additionalProperties: false,
    properties: {
      id: { bsonType: "string" },
      username: { bsonType: "string", minLength: 3, maxLength: 50 },
      password_salt: { bsonType: "string" },
      password_hash: { bsonType: "string" },
      created_at: { bsonType: ["string", "date"] },
    },
  },
  sessions: {
    bsonType: "object",
    required: ["token", "user_id", "created_at"],
    additionalProperties: false,
    properties: {
      token: { bsonType: "string" },
      user_id: { bsonType: "string" },
      created_at: { bsonType: ["string", "date"] },
      expires_at: { bsonType: ["string", "date"] },
    },
  },
  meetings: {
    bsonType: "object",
    required: ["id", "title", "owner_id", "created_at", "updated_at"],
    additionalProperties: false,
    properties: {
      id: { bsonType: "string" },
      title: { bsonType: "string", minLength: 3, maxLength: 200 },
      owner_id: { bsonType: "string" },
      created_at: { bsonType: ["string", "date"] },
      updated_at: { bsonType: ["string", "date"] },
      domains: { bsonType: "array", items: { bsonType: "string" } },
      open_questions: { bsonType: "array", items: { bsonType: "string" } },
      resolved_questions: { bsonType: "array", items: { bsonType: "string" } },
      minutes: {
        bsonType: "array",
        items: {
          bsonType: "object",
          required: ["id", "source", "text", "created_at"],
          additionalProperties: false,
          properties: {
            id: { bsonType: "string" },
            source: { enum: ["text", "pdf"] },
            filename: { bsonType: "string" },
            text: { bsonType: "string" },
            created_at: { bsonType: ["string", "date"] },
          },
        },
      },
      speaker_notes: {
        bsonType: "array",
        items: {
          bsonType: "object",
          required: ["id", "speaker", "text", "created_at"],
          additionalProperties: false,
          properties: {
            id: { bsonType: "string" },
            speaker: { bsonType: "string" },
            text: { bsonType: "string" },
            created_at: { bsonType: ["string", "date"] },
          },
        },
      },
      analysis_history: {
        bsonType: "array",
        items: {
          bsonType: "object",
          required: ["id", "created_at", "input_text", "analysis"],
          additionalProperties: false,
          properties: {
            id: { bsonType: "string" },
            created_at: { bsonType: ["string", "date"] },
            input_text: { bsonType: "string" },
            analysis: {
              bsonType: "object",
              required: [
                "status",
                "message",
                "domains",
                "questions",
                "resolved_now",
                "open_after_analysis",
              ],
              additionalProperties: false,
              properties: {
                status: { bsonType: "string" },
                message: { bsonType: "string" },
                domains: { bsonType: "array", items: { bsonType: "string" } },
                questions: { bsonType: "array", items: { bsonType: "string" } },
                resolved_now: { bsonType: "array", items: { bsonType: "string" } },
                open_after_analysis: { bsonType: "array", items: { bsonType: "string" } },
              },
            },
          },
        },
      },
    },
  },
};

const COLLECTION_INDEXES = {
  users: [
    { keys: { id: 1 }, options: { name: "uniq_users_id", unique: true } },
    { keys: { username: 1 }, options: { name: "uniq_users_username", unique: true } },
    { keys: { created_at: -1 }, options: { name: "idx_users_created_at_desc" } },
  ],
  sessions: [
    { keys: { token: 1 }, options: { name: "uniq_sessions_token", unique: true } },
    {
      keys: { user_id: 1, created_at: -1 },
      options: { name: "idx_sessions_user_created_desc" },
    },
    {
      keys: { expires_at: 1 },
      options: {
        name: "ttl_sessions_expires_at",
        expireAfterSeconds: 0,
        partialFilterExpression: { expires_at: { $exists: true } },
      },
    },
  ],
  meetings: [
    { keys: { id: 1 }, options: { name: "uniq_meetings_id", unique: true } },
    {
      keys: { owner_id: 1, updated_at: -1 },
      options: { name: "idx_meetings_owner_updated_desc" },
    },
    { keys: { owner_id: 1, title: 1 }, options: { name: "idx_meetings_owner_title" } },
  ],
};

function ensureCollection(collectionName, jsonSchema) {
  const exists = appDb.getCollectionNames().includes(collectionName);
  const validator = { $jsonSchema: jsonSchema };

  if (!exists) {
    appDb.createCollection(collectionName, {
      validator,
      validationLevel: "moderate",
      validationAction: "error",
    });
    print(`[OK] Created collection with validator: ${collectionName}`);
    return;
  }

  appDb.runCommand({
    collMod: collectionName,
    validator,
    validationLevel: "moderate",
    validationAction: "error",
  });
  print(`[OK] Updated validator: ${collectionName}`);
}

function ensureIndexes(collectionName, indexDefinitions) {
  const coll = appDb.getCollection(collectionName);
  indexDefinitions.forEach((entry) => {
    const indexName = coll.createIndex(entry.keys, entry.options);
    print(`[OK] Ensured index on ${collectionName}: ${indexName}`);
  });
}

print(`[INFO] Applying schema to database: ${dbName}`);
Object.entries(COLLECTION_SCHEMAS).forEach(([collectionName, schema]) => {
  ensureCollection(collectionName, schema);
});

Object.entries(COLLECTION_INDEXES).forEach(([collectionName, indexes]) => {
  ensureIndexes(collectionName, indexes);
});

print("[DONE] Mongo schema and indexes are ready.");
