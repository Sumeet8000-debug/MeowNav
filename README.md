# MeowResc - Tier-1 Flood Detection & Telemetry Backend

Production-grade FastAPI backend and ML pipeline for disaster response (Problem Statement AI-02).

## Quickstart

1. Install Dependencies:
   pip install -r requirements.txt

2. Train Tier-1 Flood Model:
   python ml_pipeline/train_tier1.py

3. Start FastAPI Backend:
   uvicorn backend.main:app --reload

4. API Documentation:
   Navigate to http://localhost:8000/docs to test endpoints via Swagger UI.
