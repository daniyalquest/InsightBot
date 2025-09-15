import json
import pandas as pd
import matplotlib.pyplot as plt
from collections import Counter
from wordcloud import WordCloud
import nltk
from transformers import pipeline
from pathlib import Path

nltk.download("punkt")

# ---------------------------
# File paths
# ---------------------------
data_dir = Path("data")
extracted_file = data_dir / "extracted" / "articles_20250914.json"
preprocessed_dir = data_dir / "preprocessed"
preprocessed_dir.mkdir(parents=True, exist_ok=True)
output_file = preprocessed_dir / "articles_preprocessed.json"

# ---------------------------
# Load dataset
# ---------------------------
if extracted_file.exists():
    print(f"📂 Loading dataset from {extracted_file}")
    with open(extracted_file, "r", encoding="utf-8") as f:
        data = json.load(f)
else:
    raise FileNotFoundError(f"❌ Could not find {extracted_file}")

df = pd.DataFrame(data)

# ---------------------------
# 1. Basic Stats
# ---------------------------
print("✅ Dataset Shape:", df.shape)
print("\n🔹 Articles per Source:\n", df["source"].value_counts())
print("\n🔹 Articles per Language:\n", df["language"].value_counts())

# Plot sources
df["source"].value_counts().plot(kind="barh", title="Articles per Source")
plt.tight_layout()
plt.savefig(preprocessed_dir / "stats_sources.png")
plt.close()

# Plot languages
df["language"].value_counts().plot(kind="bar", title="Articles per Language")
plt.tight_layout()
plt.savefig(preprocessed_dir / "stats_languages.png")
plt.close()

# ---------------------------
# 2. Text Length Distribution
# ---------------------------
df["length"] = df["body"].apply(lambda x: len(x.split()) if isinstance(x, str) else 0)
df["length"].plot(kind="hist", bins=50, title="Article Length Distribution")
plt.xlabel("Words per article")
plt.savefig(preprocessed_dir / "stats_length.png")
plt.close()

# ---------------------------
# 3. Word Frequency (English only)
# ---------------------------
english_texts = df[df["language"] == "en"]["body"].astype(str).tolist()
all_words = " ".join(english_texts).split()
word_freq = Counter(all_words)
print("\n🔹 Top 20 Words (EN):", word_freq.most_common(20))

# Wordcloud
if english_texts:
    wc = WordCloud(width=800, height=400, background_color="white").generate(" ".join(all_words))
    wc.to_file(preprocessed_dir / "wordcloud_en.png")

# ---------------------------
# 4. Time Distribution
# ---------------------------
if "date" in df.columns:
    df["date"] = pd.to_datetime(df["date"], errors="coerce", utc=True)
    df = df.dropna(subset=["date"])
    if not df.empty:
        df.groupby(df["date"].dt.date).size().plot(kind="line", title="Articles Over Time")
        plt.tight_layout()
        plt.savefig(preprocessed_dir / "stats_time.png")
        plt.close()
    else:
        print("⚠️ No valid dates available for time distribution plot.")

# ---------------------------
# 5. Multilingual Sentiment Analysis
# ---------------------------
print("\n🔹 Loading multilingual sentiment model...")
sentiment_analyzer = pipeline("sentiment-analysis", model="nlptown/bert-base-multilingual-uncased-sentiment")

def map_sentiment(result):
    label = result["label"]  # e.g., "5 stars"
    stars = int(label.split()[0])
    if stars <= 2:
        return "negative"
    elif stars == 3:
        return "neutral"
    else:
        return "positive"

print("🔹 Running sentiment analysis...")
results = sentiment_analyzer(df["body"].astype(str).tolist(), truncation=True)
df["sentiment"] = [map_sentiment(res) for res in results]

print("\n🔹 Sentiment Distribution:\n", df["sentiment"].value_counts())

# Plot sentiment
df["sentiment"].value_counts().plot(kind="bar", title="Sentiment Distribution")
plt.tight_layout()
plt.savefig(preprocessed_dir / "stats_sentiment.png")
plt.close()

# ---------------------------
# Save processed dataset
# ---------------------------
df.to_json(output_file, orient="records", force_ascii=False, indent=2)
print(f"✅ Preprocessing complete! Processed dataset saved as {output_file}")