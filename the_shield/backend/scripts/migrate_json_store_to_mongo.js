const dbName = process.env.MONGODB_DB_NAME || "the_shield";
const jsonPath = process.env.SHIELD_JSON_PATH || `${pwd()}/app/database/shield_store.json`;
const appDb = db.getSiblingDB(dbName);

print(`[INFO] Loading JSON store from: ${jsonPath}`);
const fs = require("fs");
const raw = fs.readFileSync(jsonPath, "utf8");
const payload = JSON.parse(raw);

const collections = ["users", "sessions", "meetings"];
collections.forEach((collectionName) => {
  const docs = Array.isArray(payload[collectionName]) ? payload[collectionName] : [];
  appDb.getCollection(collectionName).deleteMany({});
  if (docs.length > 0) {
    appDb.getCollection(collectionName).insertMany(docs, { ordered: false });
  }
  print(`[OK] ${collectionName}: ${docs.length} documents`);
});

print("[DONE] JSON store migrated to MongoDB.");
