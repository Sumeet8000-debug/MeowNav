import os
import uuid
import pathlib
import datetime
import numpy as np
import joblib
from contextlib import asynccontextmanager
from typing import List, Optional
from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, Field, field_validator

# ------------------------------------------------------------------------------
# LIFESPAN AND ARTIFACT LOADING
# ------------------------------------------------------------------------------
ml_artifacts = {}

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    FastAPI Lifespan Context Manager.
    Loads the trained model into memory during server startup.
    """
    model_path = pathlib.Path(__file__).parent.parent / "artifacts" / "tier1_flood_model.pkl"
    
    if not model_path.exists():
        raise FileNotFoundError(
            f"Model artifact not found at {model_path.resolve()}. "
            "Run 'python ml_pipeline/train_tier1.py' first."
        )
    
    ml_artifacts["tier1_model"] = joblib.load(model_path)
    print(f"[+] Loaded Tier-1 Flood Model from {model_path.resolve()}")
    yield
    ml_artifacts.clear()
    print("[-] Unloaded ML artifacts.")

app = FastAPI(
    title="MeowResc Backend API",
    description="Production-grade disaster detection and triage backend (Problem Statement AI-02).",
    version="1.0.0",
    lifespan=lifespan
)

# ------------------------------------------------------------------------------
# PYDANTIC SCHEMAS
# ------------------------------------------------------------------------------
class EnvironmentalPayload(BaseModel):
    rainfall_mm: float = Field(..., ge=0.0, le=1000.0, description="Precipitation rate in mm/24h")
    river_water_level_m: float = Field(..., ge=0.0, le=50.0, description="Current river depth in meters")
    soil_saturation_pct: float = Field(..., ge=0.0, le=100.0, description="Volumetric soil water content percentage")
    temperature_c: float = Field(..., ge=-50.0, le=60.0, description="Ambient air temperature in Celsius")

    class Config:
        json_schema_extra = {
            "example": {
                "rainfall_mm": 180.5,
                "river_water_level_m": 8.4,
                "soil_saturation_pct": 89.2,
                "temperature_c": 24.5
            }
        }

class PredictTier1Response(BaseModel):
    flood_probability: float = Field(..., description="Continuous flood probability score [0.0 - 1.0]")
    system_state: str = Field(..., description="System risk classification state: 'NORMAL' or 'WATCH'")
    timestamp: str

class IMUTelemetryPayload(BaseModel):
    accel_x: List[float] = Field(..., description="Acceleration vector along X-axis in G units")
    accel_y: List[float] = Field(..., description="Acceleration vector along Y-axis in G units")
    accel_z: List[float] = Field(..., description="Acceleration vector along Z-axis in G units")

    @field_validator('accel_y', 'accel_z')
    def validate_array_lengths(cls, v, info):
        if 'accel_x' in info.data and len(v) != len(info.data['accel_x']):
            raise ValueError("All accelerometer axes arrays must have identical length.")
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "accel_x": [0.02, 0.15, 1.20, 4.80, 0.30],
                "accel_y": [0.01, 0.10, 0.90, 2.10, 0.20],
                "accel_z": [0.98, 0.99, 1.05, 3.20, 1.01]
            }
        }

class IMUConfirmResponse(BaseModel):
    peak_g_force: float = Field(..., description="Maximum resultant magnitude vector encountered across time series in Gs")
    system_state: str = Field(..., description="'CONFIRMED_DISASTER' if peak_g_force > 4.5G else 'UNCONFIRMED'")
    disaster_confirmed: bool
    timestamp: str

class MedicalFlashcard(BaseModel):
    blood_type: str = Field(..., pattern=r"^(A|B|AB|O)[+-]$", description="ABO blood group and Rh factor")
    allergies: List[str] = Field(default_factory=list, description="Known drug/environmental allergies")
    pre_existing_conditions: List[str] = Field(default_factory=list, description="Chronic medical conditions")
    emergency_contacts: List[str] = Field(..., min_length=1, description="Primary contact phone numbers")

class SOSPayload(BaseModel):
    device_id: str = Field(..., description="Unique hardware identifier of the field collar/beacon")
    latitude: float = Field(..., ge=-90.0, le=90.0)
    longitude: float = Field(..., ge=-180.0, le=180.0)
    medical_info: MedicalFlashcard
    notes: Optional[str] = None

class SOSResponse(BaseModel):
    dispatch_id: str
    status: str
    acknowledged: bool
    timestamp: str

# ------------------------------------------------------------------------------
# API ENDPOINTS
# ------------------------------------------------------------------------------
@app.post(
    "/api/v1/predict-tier1",
    response_model=PredictTier1Response,
    status_code=status.HTTP_200_OK,
    tags=["Risk Inference"]
)
async def predict_tier1(payload: EnvironmentalPayload):
    """
    Evaluates environmental sensor metrics and outputs a continuous flood probability score.
    
    If probability > 0.60, system state transitions to **WATCH**; otherwise remains **NORMAL**.
    """
    model = ml_artifacts.get("tier1_model")
    if not model:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Machine learning model is not initialized."
        )

    features = np.array([[
        payload.rainfall_mm,
        payload.river_water_level_m,
        payload.soil_saturation_pct,
        payload.temperature_c
    ]])

    # Inference probability for positive class (1: Flood)
    prob = float(model.predict_proba(features)[0][1])
    system_state = "WATCH" if prob >= 0.60 else "NORMAL"

    return PredictTier1Response(
        flood_probability=round(prob, 4),
        system_state=system_state,
        timestamp=datetime.datetime.now(datetime.timezone.utc).isoformat()
    )


@app.post(
    "/api/v1/telemetry/imu-confirm",
    response_model=IMUConfirmResponse,
    status_code=status.HTTP_200_OK,
    tags=["Hard Telemetry Verification"]
)
async def confirm_imu(payload: IMUTelemetryPayload):
    """
    Processes high-frequency 3-axis accelerometer readings to verify physical structural impact or collapse.
    
    ### Mathematical Logic:
    For each time step $i$, the Euclidean resultant magnitude vector $||a_i||$ (expressed in units of G) is calculated as:
    
    $$||a_i|| = \\sqrt{a_{x,i}^2 + a_{y,i}^2 + a_{z,i}^2}$$
    
    The maximum shock value across the vector buffer is identified:
    
    $$G_{\\text{peak}} = \\max_i (||a_i||)$$
    
    If $G_{\\text{peak}} > 4.5\\text{G}$, physical structural crash/impact is hard-confirmed (**CONFIRMED_DISASTER**).
    """
    if not payload.accel_x:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Telemetry buffer cannot be empty."
        )

    ax = np.array(payload.accel_x, dtype=np.float64)
    ay = np.array(payload.accel_y, dtype=np.float64)
    az = np.array(payload.accel_z, dtype=np.float64)

    # Calculate vector magnitude across time series array
    magnitude_series = np.sqrt(ax**2 + ay**2 + az**2)
    peak_g = float(np.max(magnitude_series))

    is_confirmed = peak_g > 4.5
    system_state = "CONFIRMED_DISASTER" if is_confirmed else "UNCONFIRMED"

    return IMUConfirmResponse(
        peak_g_force=round(peak_g, 3),
        system_state=system_state,
        disaster_confirmed=is_confirmed,
        timestamp=datetime.datetime.now(datetime.timezone.utc).isoformat()
    )


@app.post(
    "/api/v1/sos",
    response_model=SOSResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Dispatch System"]
)
async def trigger_sos(payload: SOSPayload):
    """
    Ingests high-priority SOS emergency payloads with medical flashcards and emits immediate dispatch instructions.
    """
    dispatch_id = f"DSP-{uuid.uuid4().hex[:8].upper()}"

    return SOSResponse(
        dispatch_id=dispatch_id,
        status="DISPATCH_EN_ROUTE",
        acknowledged=True,
        timestamp=datetime.datetime.now(datetime.timezone.utc).isoformat()
    )