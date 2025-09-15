# InsightBot

**InsightBot** is a news/article aggregation, processing, and exploration platform. It allows you to fetch, clean, analyze, and visualize articles from a wide range of sources, and provides a Windows XP–inspired web interface for browsing and searching articles.

---

## Project Structure

```
insightbot/
│
├── app.py                   # Main Flask web app (browse/search articles)
├── fetch_process_upload.py  # Fetch/process/upload articles from any website (user input)
├── upload_to_mongodb.py     # Upload preprocessed articles to MongoDB
├── preprocess_articles.py   # Clean/process the raw dataset
├── insightbot_dataset_builder.py # Build raw dataset from 40+ news sites
├── requirements.txt         # Python dependencies
└── data/
    └── extracted/
        └── articles_YYYYMMDD.json  # Raw dataset (output of dataset_builder)
    └── preprocessed/
        └── articles_preprocessed.json # Cleaned dataset (output of preprocess_articles)
```

---

## Setup Instructions

### 1. Clone the Repository

```sh
git clone <your-repo-url>
cd insightbot
```

### 2. Create and Activate a Virtual Environment

```sh
python -m venv venv
# On Windows:
venv\Scripts\activate
# On Linux/Mac:
source venv/bin/activate
```

### 3. Install Dependencies

```sh
pip install -r requirements.txt
```

---

## Data Pipeline

### 1. Build Raw Dataset

Fetches articles from 40+ news sites and saves them as a raw JSON file.

```sh
python insightbot_dataset_builder.py
```
- Output: `data/extracted/articles_YYYYMMDD.json`

### 2. Preprocess Articles

Cleans, normalizes, and analyzes the raw dataset.

```sh
python preprocess_articles.py
```
- Output: `data/preprocessed/articles_preprocessed.json`

### 3. Upload to MongoDB

Uploads the preprocessed articles to your local MongoDB database.

```sh
python upload_to_mongodb.py
```

---

## Fetch and Process Articles from Any Website

You can fetch, process, and upload articles from any website (not just the built-in sources):

```sh
python fetch_process_upload.py
```
- Enter the website URL when prompted.
- The script will process and upload new articles to MongoDB.

---

## Run the Web App

The main interface is a Flask app that lets you browse, search, and fetch new articles.

### Start the App

```sh
python app.py
```
or (if you prefer Flask CLI):

```sh
set FLASK_APP=app.py   # On Windows
export FLASK_APP=app.py # On Linux/Mac
flask run
```

### Features

- **Browse all articles** in the database (with "Show More" pagination).
- **Filter by website/source** using the dropdown.
- **Search/fetch new articles** from any website (just enter the URL).
- **Responsive, Windows XP–inspired UI**.
- **Modal window** for reading articles in-app, with a link to the original source.
- **Live updates**: When fetching new articles, the UI polls for new content and displays it as soon as it's ready.

---

## MongoDB Setup

- Make sure MongoDB is running locally on `mongodb://localhost:27017`.
- The database used is `insightbot`, and the collection is `articles`.
- You can change these in the config section of each script if needed.

---

## Reference: Script Purposes

- **insightbot_dataset_builder.py**  
  Fetches and creates the raw dataset (`articles_YYYYMMDD.json`) from 40+ news sites.

- **preprocess_articles.py**  
  Cleans and processes the raw dataset, producing `articles_preprocessed.json`.

- **upload_to_mongodb.py**  
  Uploads the preprocessed articles to the MongoDB database.

- **fetch_process_upload.py**  
  Fetches, processes, and uploads articles from any user-supplied website.

- **app.py**  
  Main Flask web app. Shows all articles from the database, allows filtering, and lets users search for new articles from any website.

---

## Requirements

- Python 3.8+
- MongoDB (local or remote)
- See `requirements.txt` for all Python dependencies.

---

## Example Workflow

1. Build the dataset:
    ```
    python insightbot_dataset_builder.py
    ```
2. Preprocess the dataset:
    ```
    python preprocess_articles.py
    ```
3. Upload to MongoDB:
    ```
    python upload_to_mongodb.py
    ```
4. Run the web app:
    ```
    python app.py
    ```
5. (Optional) Fetch articles from a new website:
    ```
    python fetch_process_upload.py
    ```

---

## License

MIT License (or your chosen license)

---

## Author

Daniyal (2025)  
Inspired by Windows XP
