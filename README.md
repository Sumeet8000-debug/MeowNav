# MeowResc - AI-Powered Disaster Detection & Telemetry System (AI-02)

End-to-end disaster response system featuring a FastAPI backend, Random Forest ML risk model, telemetry verification, and an interactive Streamlit control room.

## Quickstart (Run Locally)

### 1. Install Dependencies
pip install -r requirements.txt

### 2. Train ML Model
python ml_pipeline/train_tier1.py

### 3. Launch Backend API (Terminal 1)
uvicorn backend.main:app --reload --port 8000

### 4. Launch Streamlit Dashboard (Terminal 2)
python -m streamlit run frontend/app.py