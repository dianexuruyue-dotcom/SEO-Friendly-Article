# SEO-Friendly-Article
Blog Creation Workflow V0

## SEO Content Platform MVP

This repository now provides a runnable backend MVP for:
- site/language-aware keyword planning
- article authoring and upload workflow
- strict quality checks
- collaborative review and publish steps
- post-publish indexing tracking
- role-based permissions for team collaboration

## Development setup

### Prerequisites
- Python 3.11+

### Install dependencies
1. Create and activate a virtual environment:
   - `python3 -m venv .venv`
   - `source .venv/bin/activate`
2. Install project dependencies:
   - `pip install -e .`

### Run the application
- `uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload`

### Verify the environment
In another terminal:
- `curl -s http://127.0.0.1:8000/health`
- Expected response: `{"status":"ok"}`

## Quick API usage

All protected endpoints require an `X-User-Id` header.

### 1. Create a keyword (SEO manager)
- `curl -s -X POST http://127.0.0.1:8000/keywords -H "Content-Type: application/json" -H "X-User-Id: u-seo-1" -d '{"keyword":"best seo tools","language":"en","site_id":"site-en","difficulty":35,"search_volume":1200,"intent":"commercial"}'`

### 2. Create an article task (author)
- `curl -s -X POST http://127.0.0.1:8000/articles -H "Content-Type: application/json" -H "X-User-Id: u-author-1" -d '{"title":"Best SEO Tools for 2026","site_id":"site-en","language":"en","primary_keyword":"best seo tools","content":"# Heading\nThis is a practical guide...","assignee_id":"u-author-1"}'`

### 3. Run strict quality check (editor)
- `curl -s -X POST http://127.0.0.1:8000/articles/<ARTICLE_ID>/quality-check -H "X-User-Id: u-editor-1"`

### 4. Approve and publish (reviewer/publisher)
- `curl -s -X POST http://127.0.0.1:8000/articles/<ARTICLE_ID>/review -H "Content-Type: application/json" -H "X-User-Id: u-reviewer-1" -d '{"approved":true}'`
- `curl -s -X POST http://127.0.0.1:8000/articles/<ARTICLE_ID>/publish -H "Content-Type: application/json" -H "X-User-Id: u-publisher-1" -d '{"site_base_url":"https://content.example.com"}'`

### 5. Run indexing check (SEO manager)
- `curl -s -X POST http://127.0.0.1:8000/articles/<ARTICLE_ID>/index-check -H "X-User-Id: u-seo-1"`
