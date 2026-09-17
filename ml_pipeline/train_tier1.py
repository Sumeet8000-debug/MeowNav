"""
ML Training Pipeline: Tier-1 Flood & Inundation Risk Classifier
Project: NavRakshak / MeowResc (SIH26168)
"""

# Standard library imports
import os
import pathlib
from typing import Tuple, Dict

# Third-party imports
import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    precision_score,
    recall_score,
)
from sklearn.model_selection import train_test_split


def generate_synthetic_data(n_samples: int = 5000, random_state: int = 42) -> pd.DataFrame:
    """
    Generates synthetic environmental telemetry data for flood prediction.
    
    Mathematical Risk Function:
        Risk Score = 0.40*(rain_norm^1.2) + 0.40*(river_norm^1.5) + 0.20*soil_norm + N(0, 0.05)
        Threshold: Risk Score > 0.48 -> Flood Alert (1), else Normal (0)
        
    Features:
        - rainfall_mm: Continuous [0, 300] mm/24h
        - river_water_level_m: Continuous [0.5, 12.0] meters
        - soil_saturation_pct: Continuous [0, 100] percent
        - temperature_c: Continuous [10.0, 42.0] Celsius
    """
    np.random.seed(random_state)

    rainfall_mm = np.random.uniform(0.0, 300.0, n_samples)
    river_water_level_m = np.random.uniform(0.5, 12.0, n_samples)
    soil_saturation_pct = np.random.uniform(0.0, 100.0, n_samples)
    temperature_c = np.random.uniform(10.0, 42.0, n_samples)

    # Normalized feature vectors
    rain_norm = rainfall_mm / 300.0
    river_norm = river_water_level_m / 12.0
    soil_norm = soil_saturation_pct / 100.0

    # Non-linear physical boundary formulation with Gaussian noise
    risk_score = (
        (0.40 * (rain_norm ** 1.2)) + 
        (0.40 * (river_norm ** 1.5)) + 
        (0.20 * soil_norm) + 
        np.random.normal(0, 0.05, n_samples)
    )

    flood_risk_label = (risk_score > 0.48).astype(int)

    return pd.DataFrame({
        "rainfall_mm": rainfall_mm,
        "river_water_level_m": river_water_level_m,
        "soil_saturation_pct": soil_saturation_pct,
        "temperature_c": temperature_c,
        "flood_risk": flood_risk_label
    })


def train_and_evaluate() -> Tuple[RandomForestClassifier, Dict[str, float]]:
    """
    Trains the Tier-1 Random Forest Classifier, evaluates metrics, and exports the serialized artifact.

    Returns:
        Tuple[RandomForestClassifier, Dict[str, float]]: Trained model instance and evaluation metrics dictionary.
    """
    print("[+] Generating synthetic hydro-meteorological telemetry dataset...")
    df = generate_synthetic_data(n_samples=5000)

    feature_cols = ["rainfall_mm", "river_water_level_m", "soil_saturation_pct", "temperature_c"]
    X = df[feature_cols]
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
    
    metrics: Dict[str, float] = {
        "accuracy": float(accuracy_score(y_test, y_pred)),
        "precision": float(precision_score(y_test, y_pred)),
        "recall": float(recall_score(y_test, y_pred))
    }

    print("\n" + "=" * 40)
    print("EVALUATION METRICS")
    print("=" * 40)
    print(f"Accuracy  : {metrics['accuracy']:.4f}")
    print(f"Precision : {metrics['precision']:.4f}")
    print(f"Recall    : {metrics['recall']:.4f}")
    print("\nDetailed Classification Report:\n")
    print(classification_report(y_test, y_pred))

    # Export Model Artifact
    artifacts_dir = pathlib.Path(__file__).parent.parent / "artifacts"
    artifacts_dir.mkdir(parents=True, exist_ok=True)
    model_path = artifacts_dir / "tier1_flood_model.pkl"

    joblib.dump(model, model_path)
    print(f"[+] Model artifact successfully saved to: {model_path.resolve()}")

    return model, metrics


if __name__ == "__main__":
    train_and_evaluate()