import os
import pathlib
import numpy as np
import pandas as pd
import joblib
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, precision_score, recall_score, classification_report

def generate_synthetic_data(n_samples: int = 5000, random_state: int = 42) -> pd.DataFrame:
    """
    Generates synthetic environmental telemetry data for flood prediction.
    
    Mathematical Risk Function:
    Raw Risk Score = (0.45 * rainfall_norm) + (0.35 * river_norm) + (0.20 * soil_norm) + noise
    
    Features:
    - rainfall_mm: Continuous [0, 300] mm/24h
    - river_water_level_m: Continuous [0.5, 12.0] meters
    - soil_saturation_pct: Continuous [0, 100] percent
    - temperature_c: Continuous [10.0, 42.0] Celsius
    - flood_risk_label: Binary [0: Normal, 1: Flood Alert]
    """
    np.random.seed(random_state)

    rainfall_mm = np.random.uniform(0.0, 300.0, n_samples)
    river_water_level_m = np.random.uniform(0.5, 12.0, n_samples)
    soil_saturation_pct = np.random.uniform(0.0, 100.0, n_samples)
    temperature_c = np.random.uniform(10.0, 42.0, n_samples)

    # Normalize features to [0, 1] for synthetic ground truth generation
    rain_norm = rainfall_mm / 300.0
    river_norm = river_water_level_m / 12.0
    soil_norm = soil_saturation_pct / 100.0

    # Non-linear combination with random Gaussian noise
    risk_score = (
        (0.40 * (rain_norm ** 1.2)) + 
        (0.40 * (river_norm ** 1.5)) + 
        (0.20 * soil_norm) + 
        np.random.normal(0, 0.05, n_samples)
    )

    # Threshold for binary target classification
    flood_risk_label = (risk_score > 0.48).astype(int)

    df = pd.DataFrame({
        "rainfall_mm": rainfall_mm,
        "river_water_level_m": river_water_level_m,
        "soil_saturation_pct": soil_saturation_pct,
        "temperature_c": temperature_c,
        "flood_risk": flood_risk_label
    })

    return df

def train_and_evaluate():
    print("[+] Generating synthetic dataset...")
    df = generate_synthetic_data(n_samples=5000)

    X = df[["rainfall_mm", "river_water_level_m", "soil_saturation_pct", "temperature_c"]]
    y = df["flood_risk"]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.20, random_state=42, stratify=y
    )

    print("[+] Training Tier-1 Random Forest Classifier...")
    model = RandomForestClassifier(
        n_estimators=150,
        max_depth=8,
        min_samples_split=4,
        random_state=42,
        n_jobs=-1
    )
    model.fit(X_train, y_train)

    print("[+] Evaluating Model Performance...")
    y_pred = model.predict(X_test)
    
    accuracy = accuracy_score(y_test, y_pred)
    precision = precision_score(y_test, y_pred)
    recall = recall_score(y_test, y_pred)

    print("\n" + "="*40)
    print("EVALUATION METRICS")
    print("="*40)
    print(f"Accuracy  : {accuracy:.4f}")
    print(f"Precision : {precision:.4f}")
    print(f"Recall    : {recall:.4f}")
    print("\nDetailed Classification Report:\n")
    print(classification_report(y_test, y_pred))

    # Export Model Artifact
    artifacts_dir = pathlib.Path(__file__).parent.parent / "artifacts"
    artifacts_dir.mkdir(parents=True, exist_ok=True)
    model_path = artifacts_dir / "tier1_flood_model.pkl"

    joblib.dump(model, model_path)
    print(f"[+] Model artifact successfully saved to: {model_path.resolve()}")

if __name__ == "__main__":
    train_and_evaluate()