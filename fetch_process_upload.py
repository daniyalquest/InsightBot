import re
from urllib.parse import urlparse

from newspaper import build
from pymongo import MongoClient
from langdetect import detect
from textblob import TextBlob
from transformers import pipeline

# ---------------------------
# MongoDB Config
# ---------------------------
MONGO_URI = "mongodb://localhost:27017"
DB_NAME = "insightbot"
COLLECTION_NAME = "articles"

# ---------------------------
# Utils
# ---------------------------
def clean_text(text: str) -> str:
    text = re.sub(r"http\S+", " ", text)
    text = re.sub(r"[^a-zA-Z0-9\u0600-\u06FF\u0400-\u04FF\s]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()

def detect_language(text: str) -> str:
    try:
        return detect(text)
    except:
        return "unknown"

def analyze_sentiment(text: str, lang: str) -> str:
    if lang == "en":
        polarity = TextBlob(text).sentiment.polarity
        if polarity > 0.05:
            return "positive"
        elif polarity < -0.05:
            return "negative"
        else:
            return "neutral"
    else:
        result = sentiment_model(text[:512])[0]
        stars = int(result["label"].split()[0])
        if stars <= 2:
            return "negative"
        elif stars == 3:
            return "neutral"
        else:
            return "positive"

# ---------------------------
# Load Sentiment Model
# ---------------------------
print("🔹 Loading multilingual sentiment model...")
sentiment_model = pipeline(
    "sentiment-analysis",
    model="nlptown/bert-base-multilingual-uncased-sentiment"
)

# ---------------------------
# Main Pipeline
# ---------------------------
def process_website(url: str):
    print(f"\n🌐 Fetching articles from {url} ...")
    domain = urlparse(url).netloc.replace("www.", "")

    site = build(url, memoize_articles=False)
    client = MongoClient(MONGO_URI)
    collection = client[DB_NAME][COLLECTION_NAME]

    new_articles = []
    updated_articles = 0

    for article in site.articles:  # fetch ALL articles
        try:
            article.download()
            article.parse()
            body = clean_text(article.text)
            if not body:
                continue

            # Deduplication check
            existing = collection.find_one({"url": article.url})
            if existing:
                # Update sentiment if missing
                if "sentiment" not in existing or not existing["sentiment"]:
                    lang = existing.get("language", detect_language(body))
                    sentiment = analyze_sentiment(body, lang)
                    collection.update_one(
                        {"_id": existing["_id"]},
                        {"$set": {"sentiment": sentiment}}
                    )
                    updated_articles += 1
                continue

            lang = detect_language(body)
            sentiment = analyze_sentiment(body, lang)

            record = {
                "url": article.url,
                "source": domain,
                "title": article.title,
                "body": body,
                "language": lang,
                "sentiment": sentiment,
            }
            new_articles.append(record)

        except Exception as e:
            print(f"⚠️ Skipped an article: {e}")

    # Upload only new articles to MongoDB
    if new_articles:
        collection.insert_many(new_articles)

    # Summary
    print(f"\n✅ Upload complete for {domain}:")
    print(f"- New articles added: {len(new_articles)}")
    print(f"- Old articles updated: {updated_articles}")

    # List all articles for this site
    print("\n📑 Articles from this website:")
    for art in collection.find({"source": domain}, {"title": 1, "url": 1, "_id": 0}):
        print(f"- {art['title']} → {art['url']}")

# ---------------------------
# Run
# ---------------------------
if __name__ == "__main__":
    site_url = input("🔹 Enter website URL to fetch articles: ").strip()
    if site_url:
        process_website(site_url)
    else:
        print("❌ No URL provided.")
