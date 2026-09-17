import streamlit as st
import requests
import json
import math
from datetime import datetime

# ==========================================
# PAGE CONFIGURATION
# ==========================================
st.set_page_config(
    page_title="MeowResc — AI Disaster Intelligence",
    page_icon="🐾",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ==========================================
# CUSTOM STYLING (Dark / Tech Presentation Theme)
# ==========================================
st.markdown("""
<style>
    /* Dark visual tone */
    .stApp {
        background-color: #0d1117;
        color: #c9d1d9;
    }
    
    /* Custom Card Styling */
    .card {
        background-color: #161b22;
        border: 1px solid #30363d;
        border-radius: 10px;
        padding: 20px;
        margin-bottom: 20px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
    }
    
    .card-alert-red {
        background-color: #2b0b0e;
        border: 1px solid #f85149;
        border-radius: 10px;
        padding: 20px;
        margin-bottom: 20px;
    }

    .card-alert-green {
        background-color: #0d2818;
        border: 1px solid #2ea043;
        border-radius: 10px;
        padding: 20px;
        margin-bottom: 20px;
    }

    /* Status Badges */
    .badge-normal {
        background-color: #238636;
        color: white;
        padding: 6px 14px;
        border-radius: 20px;
        font-weight: bold;
        font-size: 0.9rem;
    }

    .badge-watch {
        background-color: #d29922;
        color: white;
        padding: 6px 14px;
        border-radius: 20px;
        font-weight: bold;
        font-size: 0.9rem;
    }

    .badge-critical {
        background-color: #da3633;
        color: white;
        padding: 6px 14px;
        border-radius: 20px;
        font-weight: bold;
        font-size: 0.9rem;
        animation: pulse 1.5s infinite;
    }

    /* Metric headers */
    .metric-value {
        font-size: 2.2rem;
        font-weight: 800;
        letter-spacing: -0.5px;
    }

    .header-title {
        font-size: 2.4rem;
        font-weight: 800;
        background: linear-gradient(90deg, #58a6ff 0%, #bc8cff 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
</style>
""", unsafe_allow_html=True)


# ==========================================
# SIDEBAR & SERVER CONFIGURATION
# ==========================================
st.sidebar.image("https://img.icons8.com/color/96/cat--v1.png", width=70)
st.sidebar.title("MeowResc Control")
st.sidebar.markdown("**Problem Statement AI-02**")

backend_url = st.sidebar.text_input("Backend API Base URL", value="http://localhost:8000")

# Connection Health Check
def check_health(base_url):
    try:
        response = requests.get(f"{base_url}/docs", timeout=2)
        if response.status_code == 200:
            return True, "Connected (FastAPI Ready)"
        return True, f"Online (Status: {response.status_code})"
    except requests.exceptions.RequestException:
        return False, "Offline (Backend Unreachable)"

is_connected, health_msg = check_health(backend_url)

if is_connected:
    st.sidebar.success(f"🟢 Server State: {health_msg}")
else:
    st.sidebar.error(f"🔴 Server State: {health_msg}")
    st.sidebar.warning("⚠️ Ensure FastAPI backend is running on `http://localhost:8000`.")

st.sidebar.markdown("---")
st.sidebar.info("💡 **Judge Note:** Use the interactive controls in each tab to send payloads to the live backend server.")


# ==========================================
# API HELPER FUNCTION
# ==========================================
def make_api_post(endpoint_path, payload):
    full_url = f"{backend_url.rstrip('/')}{endpoint_path}"
    try:
        response = requests.post(full_url, json=payload, timeout=5)
        if response.status_code in [200, 201]:
            return True, response.json(), None
        else:
            return False, None, f"HTTP {response.status_code}: {response.text}"
    except requests.exceptions.ConnectionError:
        return False, None, f"Could not connect to {full_url}. Is FastAPI server running?"
    except requests.exceptions.Timeout:
        return False, None, f"Request to {full_url} timed out."
    except Exception as e:
        return False, None, f"An unexpected error occurred: {str(e)}"


# ==========================================
# MAIN DASHBOARD HEADER
# ==========================================
col_h1, col_h2 = st.columns([3, 1])
with col_h1:
    st.markdown('<p class="header-title">🐾 MeowResc Disaster Command Dashboard</p>', unsafe_allow_html=True)
    st.caption("AI-Powered Environmental Early Warning, Sensor Crash Verification & Medical SOS System")

st.markdown("---")


# ==========================================
# TABS SETUP
# ==========================================
tab1, tab2, tab3 = st.tabs([
    "🌊 Tab 1: Flood Risk Predictor",
    "💥 Tab 2: IMU Telemetry Crash Verification",
    "🚨 Tab 3: Medical Dispatch SOS"
])


# ==========================================
# TAB 1: ENVIRONMENTAL FLOOD RISK PREDICTOR
# ==========================================
with tab1:
    st.subheader("Tier-1 Environmental Flood Risk Assessment")
    st.write("Calculates real-time flood risk probability based on environmental IoT sensor inputs.")

    col_inputs, col_results = st.columns([1, 1], gap="large")

    with col_inputs:
        st.markdown("#### 🎛️ Sensor Input Controls")
        
        rainfall_mm = st.slider(
            "Rainfall (mm)",
            min_value=0.0,
            max_value=300.0,
            value=125.5,
            step=0.5,
            help="Cumulative rainfall measured over the observation window."
        )

        river_water_level_m = st.slider(
            "River Water Level (m)",
            min_value=0.5,
            max_value=12.0,
            value=6.8,
            step=0.1,
            help="Current river gauge measurement in meters."
        )

        soil_saturation_pct = st.slider(
            "Soil Saturation (%)",
            min_value=0.0,
            max_value=100.0,
            value=78.0,
            step=0.5,
            help="Percentage of moisture saturation in surrounding soil."
        )

        temperature_c = st.slider(
            "Temperature (°C)",
            min_value=10.0,
            max_value=42.0,
            value=26.5,
            step=0.5
        )

        predict_btn = st.button("🔍 Run Flood Prediction", use_container_width=True, type="primary")

    with col_results:
        st.markdown("#### 📊 Analysis Output")

        if predict_btn or 't1_result' in st.session_state:
            if predict_btn:
                payload = {
                    "rainfall_mm": float(rainfall_mm),
                    "river_water_level_m": float(river_water_level_m),
                    "soil_saturation_pct": float(soil_saturation_pct),
                    "temperature_c": float(temperature_c)
                }
                success, data, err_msg = make_api_post("/api/v1/predict-tier1", payload)
                if success:
                    st.session_state['t1_result'] = data
                    st.session_state['t1_error'] = None
                else:
                    st.session_state['t1_result'] = None
                    st.session_state['t1_error'] = err_msg

            if st.session_state.get('t1_error'):
                st.error(f"❌ Backend Request Failed: {st.session_state['t1_error']}")
            elif st.session_state.get('t1_result'):
                res = st.session_state['t1_result']
                
                # Dynamic field extractions for payload variations
                prob_score = res.get("flood_risk_score", res.get("probability", res.get("risk_score", 0.0)))
                # Normalize probability score to float [0.0 - 1.0] or [0 - 100]
                if prob_score > 1.0:
                    prob_pct = min(prob_score, 100.0)
                else:
                    prob_pct = min(prob_score * 100.0, 100.0)

                system_state = res.get("system_state", res.get("status", "NORMAL")).upper()

                # State color badges
                badge_html = '<span class="badge-normal">NORMAL</span>'
                if "WATCH" in system_state or "WARNING" in system_state:
                    badge_html = '<span class="badge-watch">WATCH</span>'
                elif "CRITICAL" in system_state or "HIGH" in system_state or "ALERT" in system_state:
                    badge_html = '<span class="badge-critical">CRITICAL</span>'

                st.markdown(f"""
                <div class="card">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <span style="font-size: 1.1rem; font-weight: 600;">System State</span>
                        {badge_html}
                    </div>
                    <hr style="border-color: #30363d;">
                    <div style="margin-top: 10px;">
                        <span style="color: #8b949e; font-size: 0.9rem;">Calculated Flood Risk Probability</span>
                        <div class="metric-value" style="color: {'#f85149' if prob_pct >= 60 else '#e3b341' if prob_pct >= 30 else '#3fb950'};">
                            {prob_pct:.1f}%
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

                st.write("**Risk Gauge Progress:**")
                st.progress(float(prob_pct / 100.0))

                with st.expander("📄 View Raw Backend Response JSON"):
                    st.json(res)
        else:
            st.info("👈 Adjust sensor values on the left and click **Run Flood Prediction** to view live analysis.")


# ==========================================
# TAB 2: HARD TELEMETRY (IMU CRASH VERIFICATION)
# ==========================================
with tab2:
    st.subheader("Hard Telemetry — IMU Crash Verification")
    st.write("Verifies high-G impact crashes using accelerometer 3-axis readings (`accel_x`, `accel_y`, `accel_z`).")

    col_preset, col_imuresult = st.columns([1, 1], gap="large")

    with col_preset:
        st.markdown("#### 🛰️ Preset Scenario Simulation")

        scenario = st.radio(
            "Select Telemetry Simulation Preset:",
            options=["Heavy Impact (>4.5G)", "Normal Movement"],
            index=0
        )

        if scenario == "Heavy Impact (>4.5G)":
            default_x = [0.8, 1.2, 5.2, 2.1, 0.4]
            default_y = [0.2, 0.5, -4.8, -1.0, 0.1]
            default_z = [9.8, 10.2, 24.5, 11.0, 9.7]
            preset_desc = "🚨 **Simulating catastrophic high-velocity collision/crash event.**"
        else:
            default_x = [0.02, 0.05, 0.11, 0.04, 0.02]
            default_y = [0.01, 0.03, 0.02, 0.05, 0.01]
            default_z = [0.98, 1.01, 0.99, 1.02, 0.98]
            preset_desc = "🟢 **Simulating standard movement/walking pattern.**"

        st.markdown(preset_desc)

        # Allow judges to preview payload
        telemetry_payload = {
            "accel_x": default_x,
            "accel_y": default_y,
            "accel_z": default_z
        }

        with st.expander("📝 Inspect Transmitted Array Payload"):
            st.json(telemetry_payload)

        # Local calculation preview
        max_g = 0.0
        for x, y, z in zip(default_x, default_y, default_z):
            mag = math.sqrt(x**2 + y**2 + z**2)
            # If acceleration is in m/s², normalize to standard g (9.81 m/s²) if necessary
            g_val = mag / 9.81 if mag > 15.0 else mag
            if g_val > max_g:
                max_g = g_val

        st.caption(f"Estimated Local Peak Force Preview: ~{max_g:.2f} G")

        verify_imu_btn = st.button("💥 Send Telemetry for Verification", use_container_width=True, type="primary")

    with col_imuresult:
        st.markdown("#### 🛡️ Verification Results")

        if verify_imu_btn or 't2_result' in st.session_state:
            if verify_imu_btn:
                success, data, err_msg = make_api_post("/api/v1/telemetry/imu-confirm", telemetry_payload)
                if success:
                    st.session_state['t2_result'] = data
                    st.session_state['t2_error'] = None
                else:
                    st.session_state['t2_result'] = None
                    st.session_state['t2_error'] = err_msg

            if st.session_state.get('t2_error'):
                st.error(f"❌ Backend Error: {st.session_state['t2_error']}")
            elif st.session_state.get('t2_result'):
                res = st.session_state['t2_result']

                calculated_peak = res.get("peak_g_force", res.get("peak_g", max_g))
                alert_status = res.get("alert_status", res.get("status", "UNCONFIRMED"))

                is_confirmed_disaster = (
                    calculated_peak >= 4.5 or 
                    "CONFIRMED" in str(alert_status).upper() or 
                    "DISASTER" in str(alert_status).upper()
                )

                if is_confirmed_disaster:
                    st.markdown(f"""
                    <div class="card-alert-red">
                        <div style="color: #f85149; font-weight: 800; font-size: 1.4rem;">
                            🚨 CONFIRMED_DISASTER ALERT TRIGGERED
                        </div>
                        <p style="margin-top: 8px; color: #f0f6fc;">
                            Impact exceeded threshold limit of <b>4.5G</b>. Automated crash protocol engaged.
                        </p>
                        <hr style="border-color: #f85149; opacity: 0.3;">
                        <div style="display: flex; gap: 30px; margin-top: 10px;">
                            <div>
                                <span style="font-size: 0.85rem; color: #8b949e;">PEAK G-FORCE</span>
                                <div style="font-size: 2rem; font-weight: 800; color: #f85149;">{calculated_peak:.2f} G</div>
                            </div>
                            <div>
                                <span style="font-size: 0.85rem; color: #8b949e;">ALERT STATUS</span>
                                <div style="font-size: 1.2rem; font-weight: 700; color: #f85149; margin-top: 8px;">
                                    {alert_status}
                                </div>
                            </div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown(f"""
                    <div class="card-alert-green">
                        <div style="color: #3fb950; font-weight: 800; font-size: 1.3rem;">
                            🟢 NORMAL OPERATION (NO CRASH)
                        </div>
                        <p style="margin-top: 8px; color: #f0f6fc;">
                            Telemetry readings remain within safe operating parameters (&lt; 4.5G).
                        </p>
                        <hr style="border-color: #2ea043; opacity: 0.3;">
                        <div style="display: flex; gap: 30px; margin-top: 10px;">
                            <div>
                                <span style="font-size: 0.85rem; color: #8b949e;">PEAK G-FORCE</span>
                                <div style="font-size: 2rem; font-weight: 800; color: #3fb950;">{calculated_peak:.2f} G</div>
                            </div>
                            <div>
                                <span style="font-size: 0.85rem; color: #8b949e;">ALERT STATUS</span>
                                <div style="font-size: 1.2rem; font-weight: 700; color: #3fb950; margin-top: 8px;">
                                    {alert_status}
                                </div>
                            </div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

                with st.expander("📄 View Backend Response Payload"):
                    st.json(res)


# ==========================================
# TAB 3: EMERGENCY DISPATCH & MEDICAL SOS
# ==========================================
with tab3:
    st.subheader("Emergency Dispatch & Medical SOS Pipeline")
    st.write("Transmits emergency coordinates and victim medical profiles to first responders.")

    col_sos_form, col_sos_disp = st.columns([1, 1], gap="large")

    with col_sos_form:
        st.markdown("#### 📋 SOS Profile Input")

        device_id = st.text_input("Device Identification Number", value="MEOW-RESC-DEV-9901")

        c1, c2 = st.columns(2)
        with c1:
            latitude = st.number_input("Latitude", value=18.5204, format="%.4f")
        with c2:
            longitude = st.number_input("Longitude", value=73.8567, format="%.4f")

        blood_type = st.selectbox(
            "Victim Blood Type",
            ["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-", "UNKNOWN"],
            index=6
        )

        allergies = st.text_input("Known Medical Allergies", value="Penicillin, Peanuts")
        
        contacts_raw = st.text_area(
            "Emergency Contacts (comma separated)",
            value="+91-9876543210, +91-9123456789"
        )

        st.markdown("<br>", unsafe_allow_html=True)
        sos_trigger_btn = st.button("🚨 TRIGGER EMERGENCY SOS", use_container_width=True, type="primary")

    with col_sos_disp:
        st.markdown("#### 🚑 Dispatch Confirmation Panel")

        if sos_trigger_btn or 't3_result' in st.session_state:
            if sos_trigger_btn:
                # Format emergency contacts list
                contacts_list = [c.strip() for c in contacts_raw.split(",") if c.strip()]
                
                sos_payload = {
                    "device_id": device_id,
                    "latitude": float(latitude),
                    "longitude": float(longitude),
                    "blood_type": blood_type,
                    "allergies": allergies,
                    "emergency_contacts": contacts_list
                }

                success, data, err_msg = make_api_post("/api/v1/sos", sos_payload)
                if success:
                    st.session_state['t3_result'] = data
                    st.session_state['t3_error'] = None
                else:
                    st.session_state['t3_result'] = None
                    st.session_state['t3_error'] = err_msg

            if st.session_state.get('t3_error'):
                st.error(f"❌ SOS Dispatch Trigger Failed: {st.session_state['t3_error']}")
            elif st.session_state.get('t3_result'):
                res = st.session_state['t3_result']

                dispatch_id = res.get("dispatch_id", res.get("sos_id", "DSP-98231-X"))
                status_txt = res.get("status", res.get("dispatch_status", "DISPATCHED"))
                timestamp = res.get("timestamp", res.get("created_at", datetime.now().strftime("%Y-%m-%d %H:%M:%S")))

                st.markdown(f"""
                <div class="card" style="border: 1px solid #58a6ff;">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <span style="color: #58a6ff; font-weight: bold; font-size: 1.1rem;">✅ DISPATCH CONFIRMED</span>
                        <span style="background-color: #1f6beb; color: white; padding: 4px 10px; border-radius: 12px; font-size: 0.8rem;">
                            ACTIVE RESPONDER EN ROUTE
                        </span>
                    </div>
                    <hr style="border-color: #30363d;">
                    
                    <table style="width: 100%; border-collapse: collapse; font-size: 0.95rem;">
                        <tr>
                            <td style="padding: 6px 0; color: #8b949e;">Dispatch ID:</td>
                            <td style="padding: 6px 0; font-weight: bold; color: #58a6ff;"><code>{dispatch_id}</code></td>
                        </tr>
                        <tr>
                            <td style="padding: 6px 0; color: #8b949e;">Status:</td>
                            <td style="padding: 6px 0; font-weight: bold; color: #3fb950;">{status_txt}</td>
                        </tr>
                        <tr>
                            <td style="padding: 6px 0; color: #8b949e;">GPS Coordinates:</td>
                            <td style="padding: 6px 0;">{latitude}, {longitude}</td>
                        </tr>
                        <tr>
                            <td style="padding: 6px 0; color: #8b949e;">Blood Type:</td>
                            <td style="padding: 6px 0; font-weight: bold; color: #f85149;">{blood_type}</td>
                        </tr>
                        <tr>
                            <td style="padding: 6px 0; color: #8b949e;">Allergies Flagged:</td>
                            <td style="padding: 6px 0;">{allergies if allergies else 'None Reported'}</td>
                        </tr>
                        <tr>
                            <td style="padding: 6px 0; color: #8b949e;">Timestamp:</td>
                            <td style="padding: 6px 0; color: #8b949e;">{timestamp}</td>
                        </tr>
                    </table>
                </div>
                """, unsafe_allow_html=True)

                st.success("📡 Medical SOS Broadcast Sent to Emergency Command Center!")

                with st.expander("📄 View Full Dispatch Response Payload"):
                    st.json(res)
        else:
            st.info("👈 Fill out the SOS form and press **TRIGGER EMERGENCY SOS** to simulate dispatch.")


# ==========================================
# FOOTER
# ==========================================
st.markdown("---")
st.caption("🐾 **MeowResc Team AI-02** | Real-Time Emergency Response System Dashboard")