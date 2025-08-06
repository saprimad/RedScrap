# RedScrap

**RedScrap** is a lightweight and customizable Python tool for collecting Reddit comments and metadata to support qualitative, netnographic, and digital ethnography research.

It enables researchers to extract and structure public discourse from specific subreddits or Reddit threads using filters such as keyword, date range, and post type.

## 🔧 Features

- Scrape Reddit comments from posts or entire subreddits
- Filter by keyword, post type, and date range
- Export data in CSV or JSON format
- Built on PRAW (Python Reddit API Wrapper)
- Ideal for netnography, thematic analysis, and public discourse studies

## 📦 Installation

Clone the repo and install dependencies:

```bash
git clone https://github.com/saprimad/RedScrap.git
cd RedScrap
pip install -r requirements.txt
```

## ⚙️ Configuration

Create a `.env` file or use environment variables:

```
REDDIT_CLIENT_ID=your_client_id
REDDIT_CLIENT_SECRET=your_client_secret
REDDIT_USER_AGENT=RedScrapAgent
```

## 🚀 Usage

Basic example (adjust as needed):

```python
from redscrap import RedScrap

scraper = RedScrap()
scraper.scrape_post("https://www.reddit.com/r/malaysia/comments/xxxxx/title/")
scraper.export_to_csv("output.csv")
```

## 📁 Output

- Comment body
- Author
- Score
- Timestamp
- Subreddit
- Parent/Thread ID

## 📝 License

This project is licensed under the MIT License.

## 👨‍🔬 Citation

If used in research, please cite:

> Tumiran, M.S. (2025). *RedScrap: A Python Tool for Netnographic Data Collection from Reddit*. (In submission to JOSS)
