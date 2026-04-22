# SEO-Friendly-Article
Blog Creation Workflow V0

## Development setup

### Prerequisites
- Python 3.11+

### Install dependencies
1. Create and activate a virtual environment:
   - `python -m venv .venv`
   - `source .venv/bin/activate`
2. Install project dependencies:
   - `pip install -e .`

### Run the application
- `uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload`

### Verify the environment
In another terminal:
- `curl -s http://127.0.0.1:8000/health`
- Expected response: `{"status":"ok"}`
