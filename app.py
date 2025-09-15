from flask import Flask, render_template_string, request, jsonify
from fetch_process_upload import process_website
from pymongo import MongoClient
import threading
import random
from urllib.parse import urlparse
from datetime import datetime

app = Flask(__name__)

# MongoDB config
MONGO_URI = "mongodb://localhost:27017"
DB_NAME = "insightbot"
COLLECTION_NAME = "articles"

client = MongoClient(MONGO_URI)
db = client[DB_NAME]
collection = db[COLLECTION_NAME]

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>InsightBot</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        html { box-sizing: border-box; }
        *, *:before, *:after { box-sizing: inherit; }
        body {
            font-family: Tahoma, Verdana, Segoe UI, Arial, sans-serif;
            background: white;
            margin: 0;
            padding: 0;
        }
        .xp-window {
            background: #ece9d8;
            border: 2px solid #000080;
            border-radius: 6px;
            width: 800px;
            max-width: 98vw;
            margin: 40px auto 0 auto;
            box-shadow: 0 0 24px #333;
        }
        .xp-titlebar {
            background: linear-gradient(to right, #0a246a 0%, #3a6ea5 100%);
            color: #fff;
            padding: 8px 16px;
            font-size: 22px;
            font-weight: bold;
            border-top-left-radius: 4px;
            border-top-right-radius: 4px;
            letter-spacing: 1px;
            border-bottom: 2px solid #000080;
            display: flex;
            align-items: center;
        }
        .xp-titlebar img {
            height: 24px;
            margin-right: 10px;
        }
        .xp-content {
            padding: 24px 32px 32px 32px;
        }
        .subtitle {
            color: #0a246a;
            margin-bottom: 18px;
            font-size: 15px;
        }
        form {
            margin-bottom: 24px;
            background: #d4d0c8;
            padding: 12px 16px;
            border-radius: 4px;
            border: 1px solid #b5b5b5;
            box-shadow: 1px 1px 0 #fff inset;
            display: flex;
            align-items: center;
            gap: 10px;
            flex-wrap: wrap;
        }
        input[type=text] {
            flex: 1 1 220px;
            min-width: 180px;
            padding: 6px;
            font-size: 15px;
            border: 1px solid #7f9db9;
            border-radius: 2px;
            background: #fff;
            color: #222;
            box-shadow: 1px 1px 0 #fff inset;
        }
        button {
            padding: 6px 18px;
            font-size: 15px;
            background: linear-gradient(to bottom, #e4e4e4 0%, #b5b5b5 100%);
            color: #222;
            border: 1px solid #7f9db9;
            border-radius: 2px;
            margin-left: 0;
            cursor: pointer;
            box-shadow: 1px 1px 0 #fff inset;
        }
        button.option-btn {
            background: linear-gradient(to bottom, #e4e4e4 0%, #b5b5b5 100%);
            color: #222;
            border: 1px solid #7f9db9;
            margin-left: 8px;
        }
        button:hover {
            background: #316ac5;
            color: #fff;
        }
        ul {
            list-style: none;
            padding: 0;
        }
        li {
            background: #fff;
            margin-bottom: 10px;
            padding: 10px 16px;
            border-radius: 3px;
            border: 1px solid #b5b5b5;
            box-shadow: 1px 1px 0 #fff inset;
            font-size: 15px;
        }
        .source {
            color: #0a246a;
            font-size: 12px;
            margin-top: 2px;
        }
        .loading {
            color: #e67e22;
            background: #fff8e1;
            border: 1px solid #e67e22;
            padding: 8px 14px;
            border-radius: 3px;
            margin-bottom: 18px;
            font-size: 15px;
        }
        h2 {
            color: #0a246a;
            margin-top: 24px;
            font-size: 18px;
            border-bottom: 1px solid #b5b5b5;
            padding-bottom: 4px;
        }
        .xp-footer {
            background: #d4d0c8;
            color: #222;
            padding: 8px 16px;
            border-top: 1px solid #b5b5b5;
            border-bottom-left-radius: 4px;
            border-bottom-right-radius: 4px;
            font-size: 13px;
            text-align: right;
        }
        a {
            color: #0a246a;
            text-decoration: underline;
        }
        a:hover {
            color: #316ac5;
        }
        /* Modal styles */
        #article-modal {
            display:none;
            position:fixed;
            z-index:1000;
            left:0; top:0;
            width:100vw; height:100vh;
            background:rgba(0,0,0,0.45);
        }
        #article-modal .modal-content {
            background:#ece9d8;
            border:2px solid #000080;
            border-radius:8px;
            width:600px;
            max-width:96vw;
            margin:60px auto;
            padding:32px;
            position:relative;
            box-shadow:0 0 24px #333;
        }
        #article-modal .close-btn {
            position:absolute;
            top:12px; right:18px;
            font-size:22px;
            color:#0a246a;
            cursor:pointer;
        }
        #modal-title {
            color:#0a246a;
            margin-top:0;
        }
        #modal-details {
            font-size:14px;
            color:#333;
            margin-bottom:16px;
        }
        #modal-body {
            font-size:16px;
            color:#222;
            background:#fff;
            border-radius:4px;
            padding:18px;
            border:1px solid #b5b5b5;
            max-height:350px;
            overflow:auto;
        }
        #modal-original-link {
            display: inline-block;
            margin-top: 18px;
            background: #0a246a;
            color: #fff !important;
            padding: 7px 18px;
            border-radius: 3px;
            text-decoration: none;
            font-weight: bold;
            font-size: 15px;
            border: 1px solid #316ac5;
            transition: background 0.2s;
        }
        #modal-original-link:hover {
            background: #316ac5;
        }
        @media (max-width: 900px) {
            .xp-window { width: 99vw; }
            #article-modal .modal-content { width: 99vw; padding: 10vw 2vw; }
        }
        @media (max-width: 600px) {
            .xp-content { padding: 10px 2vw 20px 2vw; }
            #article-modal .modal-content { width: 99vw; padding: 6vw 2vw; }
            form { flex-direction: column; gap: 8px; }
            input[type=text], button { width: 100%; min-width: 0; }
        }
    </style>
    <script>
        function showLoading() {
            document.getElementById('loading').style.display = 'block';
        }
        function showModal(article) {
            const modal = document.getElementById('article-modal');
            document.getElementById('modal-title').innerText = article.title;
            document.getElementById('modal-body').innerHTML = article.body.replace(/\\n/g, '<br>');
            document.getElementById('modal-details').innerHTML =
                `<b>Source:</b> ${article.source}<br>` +
                `<b>Language:</b> ${article.language.toUpperCase()}<br>` +
                `<b>Sentiment:</b> ${article.sentiment.charAt(0).toUpperCase() + article.sentiment.slice(1)}<br>` +
                (article.date ? `<b>Date:</b> ${article.date}<br>` : '');
            document.getElementById('modal-original-link').href = article.url;
            modal.style.display = 'block';
        }
        function attachModalEvents() {
            document.querySelectorAll('.article-link').forEach(function(link) {
                link.onclick = function(e) {
                    e.preventDefault();
                    fetch('/article_details?url=' + encodeURIComponent(this.getAttribute('data-url')))
                        .then(resp => resp.json())
                        .then(data => showModal(data));
                };
            });
        }
        document.addEventListener('DOMContentLoaded', function() {
            attachModalEvents();
            const list = document.getElementById('article-list');
            if (list) {
                const observer = new MutationObserver(attachModalEvents);
                observer.observe(list, {childList: true});
            }
            const listMain = document.getElementById('article-list-main');
            if (listMain) {
                const observerMain = new MutationObserver(attachModalEvents);
                observerMain.observe(listMain, {childList: true});
            }
        });
        window.onclick = function(event) {
            const modal = document.getElementById('article-modal');
            if (event.target == modal) {
                modal.style.display = 'none';
            }
        };
        document.addEventListener('keydown', function(e) {
            if (e.key === 'Escape') {
                document.getElementById('article-modal').style.display = 'none';
            }
        });

        // Poll for new articles when loading is true and domain is set
        let polling = false;
        function pollForArticles(domain) {
            if (!domain) return;
            polling = true;
            function fetchArticles() {
                fetch('/latest_articles?domain=' + encodeURIComponent(domain))
                    .then(resp => resp.json())
                    .then(data => {
                        const list = document.getElementById('dynamic-article-list');
                        if (list) {
                            list.innerHTML = '';
                            data.articles.forEach(function(art) {
                                let li = document.createElement('li');
                                li.innerHTML = `<a href="#" class="article-link" data-url="${art.url}">${art.title}</a>
                                    <div class="source">${art.language.toUpperCase()} | ${art.sentiment.charAt(0).toUpperCase() + art.sentiment.slice(1)}</div>`;
                                list.appendChild(li);
                            });
                            attachModalEvents();
                        }
                    });
                if (polling) setTimeout(fetchArticles, 3000); // poll every 3 seconds
            }
            fetchArticles();
        }
        function stopPolling() { polling = false; }
    </script>
</head>
<body>
    <div class="xp-window">
        <div class="xp-titlebar">
            <a href="/" style="color:inherit;text-decoration:none;flex:1;">
                InsightBot Article Explorer
            </a>
        </div>
        <div class="xp-content">
            <div class="subtitle">Search for new articles from a website or view stored articles for any site.</div>
            <form method="post" onsubmit="showLoading()">
                <input type="text" name="site_url" placeholder="Enter website URL (e.g. https://www.techradar.com/)" value="{{ site_url or '' }}">
                <button type="submit" name="action" value="fetch">Fetch New Articles</button>
                <button type="submit" name="action" value="show" class="option-btn">Show Stored Only</button>
                <select name="filter_source" onchange="this.form.submit()" style="margin-left:10px;">
                    <option value="">Filter by website...</option>
                    {% for src in sources %}
                        <option value="{{ src }}" {% if src == selected_source %}selected{% endif %}>{{ src }}</option>
                    {% endfor %}
                </select>
            </form>
            <div id="loading" class="loading" style="display:{{ 'block' if loading else 'none' }};">
                Please wait...
            </div>
            {% if articles %}
                <h2>Articles{% if domain %} from {{ domain }}{% endif %}</h2>
                <ul id="dynamic-article-list">
                {% for art in articles %}
                    <li>
                        <a href="#" class="article-link" data-url="{{ art['url'] }}">{{ art['title'] }}</a>
                        <div class="source">{{ art['language']|upper }} | {{ art['sentiment']|capitalize }}</div>
                    </li>
                {% endfor %}
                </ul>
                <script>
                {% if loading and domain %}
                    pollForArticles("{{ domain }}");
                {% else %}
                    stopPolling();
                {% endif %}
                </script>
            {% elif domain %}
                <p>No articles found for this site.</p>
            {% else %}
                <h2>All Articles</h2>
                <ul id="article-list">
                {% for art in all_articles %}
                    <li>
                        <a href="#" class="article-link" data-url="{{ art['url'] }}">{{ art['title'] }}</a>
                        <div class="source">{{ art['source'] }} | {{ art['language']|upper }} | {{ art['sentiment']|capitalize }}</div>
                    </li>
                {% endfor %}
                </ul>
                <button id="show-more-btn" style="display: block; margin: 0 auto;">Show More</button>
                <script>
                let offset = {{ initial_count }};
                document.getElementById('show-more-btn').onclick = function() {
                    fetch('/more_articles?offset=' + offset)
                        .then(response => response.json())
                        .then(data => {
                            const list = document.getElementById('article-list');
                            data.articles.forEach(function(art) {
                                let li = document.createElement('li');
                                li.innerHTML = `<a href="#" class="article-link" data-url="${art.url}">${art.title}</a>
                                    <div class="source">${art.source} | ${art.language.toUpperCase()} | ${art.sentiment.charAt(0).toUpperCase() + art.sentiment.slice(1)}</div>`;
                                list.appendChild(li);
                            });
                            offset += data.count;
                            if (!data.has_more) {
                                document.getElementById('show-more-btn').style.display = 'none';
                            }
                            // Re-attach modal events to new links
                            attachModalEvents();
                        });
                };
                </script>
            {% endif %}
        </div>
        <div class="xp-footer">
            InsightBot &copy; 2025 | Daniyal
        </div>
    </div>
    <div id="article-modal">
        <div class="modal-content">
            <span class="close-btn" onclick="document.getElementById('article-modal').style.display='none'">&times;</span>
            <h2 id="modal-title"></h2>
            <div id="modal-details"></div>
            <div id="modal-body"></div>
            <a id="modal-original-link" href="#" target="_blank">View Original Article</a>
        </div>
    </div>
</body>
</html>
"""

def async_process_website(site_url):
    thread = threading.Thread(target=process_website, args=(site_url,))
    thread.daemon = True
    thread.start()

@app.route("/", methods=["GET", "POST"])
def index():
    articles = []
    all_articles = []
    domain = None
    site_url = ""
    loading = False
    initial_count = 10

    # Get all unique sources for the filter dropdown
    sources = sorted(collection.distinct("source"))

    selected_source = request.form.get("filter_source", "") if request.method == "POST" else ""

    if request.method == "POST":
        site_url = request.form.get("site_url", "").strip()
        action = request.form.get("action")
        # If a filter is selected, show only articles from that source
        if selected_source:
            articles = list(collection.find(
                {"source": selected_source},
                {"title": 1, "url": 1, "language": 1, "sentiment": 1, "_id": 0, "source": 1}
            ))
            domain = selected_source
        elif site_url:
            domain = urlparse(site_url).netloc.replace("www.", "")
            articles = list(collection.find(
                {"source": domain},
                {"title": 1, "url": 1, "language": 1, "sentiment": 1, "_id": 0, "source": 1}
            ))
            if action == "fetch":
                loading = True
                async_process_website(site_url)
    else:
        all_articles = list(collection.aggregate([
            {"$sample": {"size": initial_count}},
            {"$project": {"title": 1, "url": 1, "language": 1, "sentiment": 1, "source": 1, "_id": 0}}
        ]))

    return render_template_string(
        HTML_TEMPLATE,
        articles=articles,
        all_articles=all_articles,
        domain=domain,
        site_url=site_url,
        loading=loading,
        initial_count=initial_count,
        sources=sources,
        selected_source=selected_source
    )

# Endpoint to serve more articles for 'Show More' button
@app.route("/more_articles")
def more_articles():
    offset = int(request.args.get("offset", 0))
    batch_size = 10
    total_count = collection.count_documents({})
    has_more = offset + batch_size < total_count
    articles = list(collection.aggregate([
        {"$sample": {"size": batch_size}},
        {"$project": {"title": 1, "url": 1, "language": 1, "sentiment": 1, "source": 1, "_id": 0}}
    ]))
    return jsonify({
        "articles": articles,
        "count": len(articles),
        "has_more": has_more
    })

# Endpoint to serve latest articles for a domain (for polling)
@app.route("/latest_articles")
def latest_articles():
    domain = request.args.get("domain")
    if not domain:
        return jsonify({"articles": []})
    articles = list(collection.find(
        {"source": domain},
        {"title": 1, "url": 1, "language": 1, "sentiment": 1, "_id": 0, "source": 1}
    ).sort("_id", -1).limit(30))
    return jsonify({"articles": articles})

@app.route("/article_details")
def article_details():
    url = request.args.get("url")
    article = collection.find_one({"url": url})
    if not article:
        return jsonify({"error": "Not found"}), 404

    # Convert date if it's a timestamp in milliseconds
    date_val = article.get("date", "")
    date_str = ""
    if isinstance(date_val, (int, float)):
        try:
            # Convert milliseconds to seconds
            date_str = datetime.utcfromtimestamp(date_val / 1000).strftime("%Y-%m-%d %H:%M")
        except Exception:
            date_str = str(date_val)
    elif isinstance(date_val, str):
        date_str = date_val

    return jsonify({
        "title": article.get("title", ""),
        "body": article.get("body", ""),
        "source": article.get("source", ""),
        "language": article.get("language", ""),
        "sentiment": article.get("sentiment", ""),
        "date": date_str,
        "url": article.get("url", "")
    })

if __name__ == "__main__":
    app.run(debug=True)