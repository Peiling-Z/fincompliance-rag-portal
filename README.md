# FinCompliance RAG Portal

End-to-end financial compliance Q&A system (RAG). Includes:
- Document upload → chunk/ingest → vector DB
- REST API with FastAPI
- Streamlit portal UI
- Dockerfile + docker-compose
- Terraform (GCP bucket) + CI workflow

## Quickstart
```bash
cp .env.example .env
# Optionally start a local vector DB or configure remote
docker-compose up --build
# API on http://localhost:8000, UI on http://localhost:8501
```
