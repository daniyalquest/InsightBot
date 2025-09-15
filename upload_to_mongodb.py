import json
from pymongo import MongoClient

# ---------------------------
# Config
# ---------------------------
MONGO_URI = "mongodb://localhost:27017"   # Change if using Atlas or remote Mongo
DB_NAME = "insightbot"
COLLECTION_NAME = "articles"
DATASET_PATH = "data/preprocessed/articles_preprocessed.json"

# ---------------------------
# Connect to MongoDB
# ---------------------------
client = MongoClient(MONGO_URI)
db = client[DB_NAME]
collection = db[COLLECTION_NAME]

# ---------------------------
# Load dataset
# ---------------------------
with open(DATASET_PATH, "r", encoding="utf-8") as f:
    articles = json.load(f)

print(f"Loaded {len(articles)} articles from {DATASET_PATH}")

# ---------------------------
# Insert into MongoDB
# ---------------------------
# Optional: drop old collection to start fresh
collection.drop()

# Insert all articles
result = collection.insert_many(articles)

print(f"✅ Inserted {len(result.inserted_ids)} articles into {DB_NAME}.{COLLECTION_NAME}")
