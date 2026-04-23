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

### Bootstrap users
- The system preloads admin user `id=1` at startup.
- Create additional users using admin header:
  - `curl -s -X POST http://127.0.0.1:8000/users -H "Content-Type: application/json" -H "X-User-Id: 1" -d '{"name":"SEO","role":"seo_manager"}'`

### Create a site
- `curl -s -X POST http://127.0.0.1:8000/sites -H "Content-Type: application/json" -H "X-User-Id: 1" -d '{"name":"Global Site","domain":"example.com","default_language":"en","supported_languages":["en","fr"]}'`

### Create a keyword
- `curl -s -X POST http://127.0.0.1:8000/keywords -H "Content-Type: application/json" -H "X-User-Id: 2" -d '{"site_id":1,"language":"en","keyword":"seo content workflow","intent":"informational","search_volume":2600,"difficulty":42,"priority":8,"cluster":"workflow"}'`

### Create article and run flow
- Create article:
  - `curl -s -X POST http://127.0.0.1:8000/articles -H "Content-Type: application/json" -H "X-User-Id: 3" -d '{"site_id":1,"language":"en","title":"How to Build a Strict SEO Content Workflow That Scales","slug":"strict-seo-content-workflow","content":"# SEO\n## Plan\n...","author":"Alice","author_id":3,"assignee_id":4,"primary_keyword_id":1,"primary_keyword":"seo content workflow","secondary_keywords":["seo workflow"]}'`
- Quality check:
  - `curl -s -X POST http://127.0.0.1:8000/articles/1/quality-check -H "X-User-Id: 4"`
- Submit/review/publish:
  - `curl -s -X POST http://127.0.0.1:8000/articles/1/submit-review -H "X-User-Id: 4"`
  - `curl -s -X POST http://127.0.0.1:8000/articles/1/review -H "Content-Type: application/json" -H "X-User-Id: 5" -d '{"review_step":"editorial","approved":true}'`
  - `curl -s -X POST http://127.0.0.1:8000/articles/1/publish -H "X-User-Id: 6"`
- Indexing check:
  - `curl -s -X POST http://127.0.0.1:8000/articles/1/indexing-check -H "Content-Type: application/json" -H "X-User-Id: 2" -d '{"day_offset":7}'`
