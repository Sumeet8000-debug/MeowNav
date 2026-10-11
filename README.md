# 🐾 MEOWNAV (NavRakshak Pipeline)
> **Smart India Hackathon (SIH) 2026 Submission**[cite: 1, 2, 6]  
> **Theme:** Smart Mobility & Infrastructure (Software)[cite: 1]  
> **Problem Statement ID:** SIH26168 — Navigation in GPS-Denied Environments (Tunnels, Urban Canyons, Underground Parking)[cite: 1]  
> **Team Name:** MeowMons (Team ID: 54)[cite: 1]  
> **Live Demo:** [https://meowresc.streamlit.app](https://meowresc.streamlit.app)[cite: 2]

---

## 📌 Problem Statement Overview
Satellites require direct line-of-sight. In "urban canyons" (high-rises), tunnels, or underground multi-level parking, signals are blocked, reflected (multipath interference), or completely degraded[cite: 2]. This causes routing failures for delivery riders, pin freezes for ride-hailing drivers, and loss of precision tracking for emergency responders[cite: 2].

---

## 🚀 Proposed Solution & Core Architecture
MEOWNAV is a lightweight, on-device mobile pipeline that seamlessly takes over when GNSS signals drop, keeping tracking accurate using only built-in phone sensors[cite: 2]:

1. **AI-Powered Sensor Denoising:** Strips high-frequency vibration and sensor bias from raw smartphone accelerometer and gyroscope streams at 10 Hz[cite: 2, 3].
2. **Physics-Constrained Kalman Filtering:** Fuses sensor data with Non-Holonomic Constraints (NHC) and Zero-Velocity Updates (ZUPT) to bound drift strictly under the 10% target[cite: 2, 4].
3. **Offline Map-Matching (OSM + HMM):** Uses cached OpenStreetMap data and a Viterbi algorithm to probabilistically snap position estimates onto the correct road layout[cite: 2, 3].

---

## 🛠️ Technical Stack
* **Core Language & Math:** Python, NumPy, SciPy, Pandas[cite: 3]
* **Machine Learning & Edge AI:** PyTorch, ONNX Runtime / TensorFlow Lite[cite: 3]
* **Filtering & State Estimation:** FilterPy, Custom ESKF Implementation[cite: 3]
* **Geospatial & Map-Matching:** OSMnx, OpenStreetMap API, NetworkX[cite: 3]
* **Frontend & Visualization:** Streamlit, Leaflet/PyDeck rendering[cite: 3]

---

## ⚙️ Local Installation & Setup

```bash
# 1. Clone the repository
git clone https://github.com/Sumeet8000-debug/MeowResc.git
cd MeowResc

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run the application
streamlit run frontend/app.py
