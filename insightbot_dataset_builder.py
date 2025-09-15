"""
insightbot_dataset_builder.py
Builds a full dataset from 40 news sites as per SRS.
"""

import os, re, json, requests, pandas as pd
from bs4 import BeautifulSoup
from datetime import datetime
from urllib.parse import urljoin

# ------------------------
# Base + Extractors (reuse from site_extractors.py)
# ------------------------
# 👉 Import your full set of 40 extractors here
from extractors.site_extractors import extract_article_from_site

# ------------------------
# Feed definitions
# ------------------------
RSS_FEEDS = {
    "CNN": ["http://rss.cnn.com/rss/cnn_topstories.rss"],
    "BBC": ["http://feeds.bbci.co.uk/news/rss.xml"],
    "New York Times": ["https://rss.nytimes.com/services/xml/rss/nyt/HomePage.xml"],
    "The Guardian": ["https://www.theguardian.com/international/rss"],
    "Reuters": ["https://www.reuters.com/rssFeed/topNews/"],
    "Washington Post": ["https://feeds.washingtonpost.com/rss/rss_politics"],
    "Forbes": ["https://www.forbes.com/real-time/feed2/"],
    "TechCrunch": ["https://techcrunch.com/feed/"],
    "The Next Web": ["https://thenextweb.com/feed/"],
    "Medium": ["https://medium.com/feed/"],
    "Dev.to": ["https://dev.to/feed"],
    "Mashable": ["https://mashable.com/feed"],
    "Wall Street Journal": ["https://feeds.a.dj.com/rss/RSSWorldNews.xml"],
    "Wired": ["https://www.wired.com/feed/rss"],
    "NPR": ["https://feeds.npr.org/1001/rss.xml"],
    "Vox": ["https://www.vox.com/rss/index.xml"],
    "Bloomberg": ["https://www.bloomberg.com/feed/podcast/onboard.xml"],
    "Seeking Alpha": ["https://seekingalpha.com/feed.xml"],
    "Engadget": ["https://www.engadget.com/rss.xml"],
    "The Verge": ["https://www.theverge.com/rss/index.xml"],
    "Financial Times": ["https://www.ft.com/rss/home"],
    "Ars Technica": ["https://arstechnica.com/feed/"],
    "CNET": ["https://www.cnet.com/rss/news/"],
    "Slashdot": ["https://rss.slashdot.org/Slashdot/slashdotMain"],
    "HuffPost": ["https://www.huffpost.com/section/front-page/feed"],
    "Al Jazeera": ["https://www.aljazeera.net/xml/rss/all"],
    "Sky News Arabia": ["https://www.skynewsarabia.com/sitemap.xml"],  # use sitemap
    "Al Arabiya": ["https://www.alarabiya.net/ar/rss"],
    "Akhbaar24": ["https://www.akhbaar24.com/rss"],
    "Middle East Online": [],  # manual crawl needed
    "The National": ["https://www.thenationalnews.com/uae/rss-feeds-1.536712"],
    "Arabic CNN": ["https://arabic.cnn.com/sitemap.xml"],  # use sitemap
    "BBC Arabic": ["https://www.bbc.com/arabic/index.xml"],
    "Masaar": [],  # manual crawl needed
    "9elp": [],  # manual crawl needed
    "RT": ["https://www.rt.com/rss/"],
    "TASS": ["https://tass.com/rss/v2.xml"],
    "RBC": ["https://rssexport.rbc.ru/rbcnews/news"],
    "Meduza": ["https://meduza.io/rss/en"],
    "Echo Moscow": ["https://echo.msk.ru/sitemap.xml"],  # use sitemap
}

# ------------------------
# Fetch article URLs from RSS
# ------------------------
def fetch_article_urls(feed_url, limit=50):
    try:
        r = requests.get(feed_url, timeout=15, headers={"User-Agent":"InsightBot/1.0"})
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "xml")
        urls = [item.find("link").text.strip() for item in soup.find_all("item")]
        return urls[:limit]
    except Exception as e:
        print(f"⚠️ RSS fetch failed: {feed_url} -> {e}")
        return []

# ------------------------
# Fetch article URLs from Sitemap
# ------------------------
def fetch_from_sitemap(sitemap_url, limit=50):
    try:
        r = requests.get(sitemap_url, timeout=15, headers={"User-Agent":"InsightBot/1.0"})
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "xml")
        urls = [loc.text.strip() for loc in soup.find_all("loc")]
        # Filter for article URLs (optional: add more sophisticated filtering)
        article_urls = [u for u in urls if re.search(r'/\d{4}/\d{2}/\d{2}/|/news/|/article/', u)]
        return article_urls[:limit]
    except Exception as e:
        print(f"⚠️ Sitemap fetch failed: {sitemap_url} -> {e}")
        return []

# ------------------------
# Enhance extraction with SRS fields
# ------------------------
def enrich_article(record, soup):
    # Author
    author = None
    for k in ["author", "dc.creator"]:
        a = soup.find("meta", attrs={"name":k})
        if a and a.get("content"):
            author = a["content"].strip(); break
    if not author:
        byline = soup.find(class_=re.compile("byline|author", re.I))
        if byline: author = byline.get_text(" ", strip=True)

    # Category
    category = None
    for k in ["article:section", "section", "category"]:
        c = soup.find("meta", attrs={"name":k}) or soup.find("meta", attrs={"property":k})
        if c and c.get("content"): category = c["content"]; break

    # Tags
    tags = []
    kw = soup.find("meta", attrs={"name":"keywords"})
    if kw and kw.get("content"):
        tags = [t.strip() for t in kw["content"].split(",")]

    # Summary (first 2 sentences)
    sentences = re.split(r'(?<=[.!?]) +', record["body"])
    summary = " ".join(sentences[:2]) if sentences else ""

    record.update({
        "author": author or "",
        "category": category or "",
        "tags": tags,
        "summary": summary
    })
    return record

# ------------------------
# Runner
# ------------------------
if __name__=="__main__":
    os.makedirs("data/extracted", exist_ok=True)
    records=[]

    for source, feeds in RSS_FEEDS.items():
        for feed in feeds:
            print(f"\n📡 Fetching from {source} RSS: {feed}")
            if feed.endswith('.xml') and 'rss' not in feed:
                urls = fetch_from_sitemap(feed, limit=20)
            else:
                urls = fetch_article_urls(feed, limit=20)  # limit per feed
            for url in urls:
                try:
                    r = requests.get(url, headers={"User-Agent":"InsightBot/1.0"}, timeout=20)
                    r.raise_for_status()
                    html = r.text
                    rec = extract_article_from_site(html, url, source)
                    soup = BeautifulSoup(html, "html.parser")
                    rec = enrich_article(rec, soup)
                    records.append(rec)
                    print(f"✅ {source}: {rec['title'][:70]}")
                except Exception as e:
                    print(f"❌ Failed {url}: {e}")

    if records:
        df = pd.DataFrame(records)
        ts = datetime.now().strftime("%Y%m%d")
        csv_path = f"data/extracted/articles_{ts}.csv"
        json_path = f"data/extracted/articles_{ts}.json"
        df.to_csv(csv_path, index=False, encoding="utf-8")
        df.to_json(json_path, orient="records", force_ascii=False, indent=2)
        print(f"\n✅ Dataset saved:\n- {csv_path}\n- {json_path}")
    else:
        print("⚠️ No records extracted.")
