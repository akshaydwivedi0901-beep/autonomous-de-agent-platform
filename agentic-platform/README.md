# Agentic Platform (scaffold)

This is a minimal scaffold for the Agentic Platform microservice.

Structure:
- `app/` application code
- `tests/` simple pytest tests
- `docker/` Dockerfile
- `terraform/` minimal terraform files

Run locally:

1. python -m venv .venv
2. source .venv/bin/activate
3. pip install -r requirements.txt
4. uvicorn app.main:app --reload
