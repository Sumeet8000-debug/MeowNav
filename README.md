<div align="center">

# Disaster Response & Telemetry Backend (Team MeowMons)
### Problem Statement: SIH26168 | Smart India Hackathon

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110%2B-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Scikit-Learn](https://img.shields.io/badge/Scikit--Learn-1.4%2B-F7931E?style=for-the-badge&logo=scikit-learn&logoColor=white)](https://scikit-learn.org/)
[![PyTorch](https://img.shields.io/badge/PyTorch-2.2%2B-EE4C2C?style=for-the-badge&logo=pytorch&logoColor=white)](https://pytorch.org/)

</div>

---

## 📌 Executive Pitch & Architecture Briefing
> **Official SIH Deck & Technical Document:**  
> 📄 **[Download Presentation: NavRakshak_SIH26168_Redesigned_v2.pdf](./NavRakshak_SIH26168_Redesigned_v2.pdf)**

---

## 🏛️ System Architecture

| Component | Technology | Specification / Role |
| :--- | :--- | :--- |
| **Server Engine** | **FastAPI + Uvicorn** | High-throughput asynchronous ASGI microservice with sub-20ms latency. |
| **ML Pipeline** | **Scikit-Learn (RandomForest)** | Non-linear Tier-1 environmental breaking-point and flood inundation probability engine. |
| **Validation Layer** | **Pydantic v2** | Strict schema validation, mathematical bounds enforcement, and JSON serializing. |
| **Telemetry Ingestion**| **NumPy + Inertial Math** | Tri-axial MEMS accelerometer peak acceleration calculation $(\|\mathbf{a}\| = \sqrt{a_x^2 + a_y^2 + a_z^2})$. |

---

## 📡 API Endpoints & Mathematical Thresholds

### 1. `POST /predict-tier1`
* **Purpose:** Evaluates river hydro-transducers, barometric drop, and rainfall rates for predictive disaster escalation.
* **Decision Rule:** $P(\text{Disaster} \mid \mathbf{x}) \ge 0.60 \implies \text{CRITICAL ALERT}$.

### 2. `POST /telemetry/imu-confirm`
* **Purpose:** Validates structural impact, building collapse, or landslide impacts using smartphone MEMS sensors.
* **Mathematical Bound:** Triggers when resultant impact vector $\|\mathbf{a}\| = \sqrt{a_x^2 + a_y^2 + a_z^2} \ge 4.5g$.

### 3. `POST /sos`
* **Purpose:** Ingests high-priority civil distress packets, automatically logging medical triage parameters (blood group, allergies) and activating low-power BLE/LoRa mode.

---

/api/v1/predict-tier1
/api/v1/telemetry/imu-confirm
/api/v1/sos

## 🚀 Quick Start (Local Execution)

```bash
# 1. Clone the repository and enter directory
git clone https://github.com/your-org/meowresc-backend.git
cd meowresc-backend

# 2. Install production dependencies
pip install -r requirements.txt

# 3. Train the Tier-1 ML artifact and launch ASGI server
python train_tier1.py
uvicorn main:app --host 0.0.0.0 --port 8000 --reload