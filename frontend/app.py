import streamlit as st
import pandas as pd
import time
import math
import random
import pydeck as pdk
from datetime import datetime

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="MeowResc | Disaster Response C4I",
    page_icon="🚨",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- STATE MANAGEMENT (SHARED GLOBALLY BETWEEN VICTIM & RESCUER) ---
if 'role' not in st.session_state:
    st.session_state.role = None

if 'disaster_type' not in st.session_state:
    st.session_state.disaster_type = "Flood"

if 'hazard_level' not in st.session_state:
    st.session_state.hazard_level = 10  # 0 to 100% scale

if 'sos_active' not in st.session_state:
    st.session_state.sos_active = False

if 'radar_step' not in st.session_state:
    st.session_state.radar_step = 0

if 'auto_pulse' not in st.session_state:
    st.session_state.auto_pulse = True

if 'sos_filter_only' not in st.session_state:
    st.session_state.sos_filter_only = False

# --- REPRODUCIBLE CIVILIAN DATASET FOR RESCUE MAP ---
if 'citizens_dataset' not in st.session_state:
    random.seed(42)
    names = ["Aarav Sharma", "Pooja Patil", "Rahul Deshmukh", "Ananya Kulkarni", "Vikram Shinde", 
             "Neha Joshi", "Amit Gokhale", "Sneha Pawar", "Rohan More", "Priyanka Chavan",
             "Suresh Gaikwad", "Tanvi Sawant", "Kavita Bhave", "Deepak Thorat", "Isha Apte"]
    allergies_list = ["Penicillin Allergy", "Severe Asthma (Needs Inhaler)", "Insulin Diabetic", 
                      "Sulfa Drugs Allergy", "Hypertension / Cardiac", "Latex Allergy", "None"]
    blood_types = ["O+", "O-", "A+", "A-", "B+", "B-", "AB+"]

    citizens = []
    base_lat, base_lon = 18.5808, 73.9787

    for i in range(120):
        offset_lat = (random.random() - 0.5) * 0.032
        offset_lon = (random.random() - 0.5) * 0.036
        c_lat = base_lat + offset_lat
        c_lon = base_lon + offset_lon
        
        d_km = round(6371.0 * 2 * math.asin(math.sqrt(
            math.sin(math.radians(offset_lat)/2)**2 + 
            math.cos(math.radians(base_lat)) * math.cos(math.radians(c_lat)) * math.sin(math.radians(offset_lon)/2)**2
        )), 2)

        c_name = f"{random.choice(names)} #{100 + i}"
        c_blood = random.choice(blood_types)
        c_age = random.randint(14, 82)
        c_allergies = random.choice(allergies_list)
        battery = f"{random.randint(8, 98)}%"

        citizens.append({
            "id": f"CIT-{2000 + i}",
            "name": c_name,
            "lat": c_lat,
            "lon": c_lon,
            "orig_sos": (i % 2 == 0) or (d_km < 0.6),
            "blood_type": c_blood,
            "age": c_age,
            "allergies": c_allergies,
            "battery": battery,
            "dist_km": d_km
        })
    st.session_state.citizens_dataset = citizens

def set_role(role_name):
    st.session_state.role = role_name

def calculate_distance(lat1, lon1, lat2, lon2):
    R = 6371.0 
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2)**2
    c = 2 * math.asin(math.sqrt(a))
    return round(R * c, 2)

# --- DYNAMIC BACKGROUND & GLOBAL STYLES ---
if st.session_state.hazard_level >= 80 or st.session_state.sos_active:
    bg_gradient = "linear-gradient(160deg, #450a0a 0%, #1e1b4b 50%, #020617 100%)"
    fallback_color = "#020617"
else:
    bg_gradient = "linear-gradient(150deg, #000000 0%, #0a192f 35%, #172554 70%, #020617 100%)"
    fallback_color = "#020617"

st.markdown(f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700;800&family=Mulish:wght@400;600;700;800&display=swap');

    html, body, [class*="css"], .stMarkdown, .stButton button, .stMetric {{
        font-family: 'Mulish', 'Cairo', sans-serif !important;
    }}

    html, body, .stApp, [data-testid="stAppViewContainer"], [data-testid="stApp"] {{
        background: {bg_gradient} !important;
        background-color: {fallback_color} !important;
        background-attachment: fixed !important;
        min-height: 100vh !important;
        color: #f8fafc !important;
    }}

    [data-testid="stHeader"], [data-testid="stToolbar"], [data-testid="stMain"],
    [data-testid="stAppViewBlockContainer"], section.main, .main, .block-container {{
        background: transparent !important;
        background-color: transparent !important;
    }}
    
    footer {{ visibility: hidden; }}

    div[data-testid="stVerticalBlockBorderWrapper"] {{
        background: rgba(15, 23, 42, 0.92) !important;
        border: 1px solid rgba(255, 255, 255, 0.15) !important;
        border-radius: 18px !important;
        box-shadow: 0 14px 35px rgba(0, 0, 0, 0.6) !important;
        backdrop-filter: blur(16px) !important;
        padding: 22px !important;
        color: #f8fafc !important;
        margin-bottom: 20px;
    }}

    .hq-stat {{
        background: rgba(2, 6, 23, 0.75);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 12px;
        padding: 12px 16px;
        text-align: center;
    }}
    .hq-stat-num {{
        font-size: 1.8rem;
        font-weight: 800;
        margin-bottom: 2px;
    }}
    .hq-stat-label {{
        font-size: 0.75rem;
        color: #94a3b8;
        text-transform: uppercase;
        letter-spacing: 0.06em;
    }}

    [data-testid="stMetricValue"] {{
        color: #38bdf8 !important;
        font-weight: 800 !important;
    }}
    [data-testid="stMetricLabel"] p {{
        color: #94a3b8 !important;
        font-weight: 600 !important;
    }}

    .pulse-pill {{
        display: inline-block;
        padding: 6px 14px;
        border-radius: 20px;
        font-size: 12px;
        font-weight: 700;
        margin-bottom: 10px;
    }}
    .pulse-pill-expanding {{
        background: rgba(239, 68, 68, 0.25);
        color: #fca5a5;
        border: 1px solid #ef4444;
    }}
    .pulse-pill-shrinking {{
        background: rgba(234, 179, 8, 0.2);
        color: #fde047;
        border: 1px solid #eab308;
    }}

    .popup-engine {{
        border-radius: 10px;
        padding: 12px 16px;
        margin-bottom: 14px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.35);
        animation: pulse-border 1.8s infinite;
    }}
    .popup-dr {{
        background: rgba(8, 145, 178, 0.22);
        border: 1px solid #06b6d4;
        border-left: 5px solid #06b6d4;
        color: #e0f2fe;
    }}
    .popup-battery {{
        background: rgba(217, 119, 6, 0.22);
        border: 1px solid #f59e0b;
        border-left: 5px solid #f59e0b;
        color: #fef3c7;
    }}

    .alert-box-safe {{
        background: rgba(34, 197, 94, 0.15);
        border-left: 4px solid #22c55e;
        border-radius: 8px; padding: 12px 16px; margin-top: 10px;
    }}
    .alert-box-watch {{
        background: rgba(234, 179, 8, 0.15);
        border-left: 4px solid #eab308;
        border-radius: 8px; padding: 12px 16px; margin-top: 10px;
    }}
    .alert-box-disaster {{
        background: rgba(239, 68, 68, 0.25);
        border-left: 4px solid #ef4444;
        border-radius: 8px; padding: 12px 16px; margin-top: 10px;
        animation: pulse-border 1.5s infinite;
    }}
    @keyframes pulse-border {{
        0% {{ border-color: #ef4444; }}
        50% {{ border-color: #fca5a5; }}
        100% {{ border-color: #ef4444; }}
    }}
</style>
""", unsafe_allow_html=True)


# =========================================================
# VIEW 1: LANDING PAGE
# =========================================================
def render_landing_page():
    st.markdown("""
    <style>
        .prototype-warning {
            background-color: rgba(15, 23, 42, 0.9); backdrop-filter: blur(10px);
            padding: 15px 20px; border-radius: 10px; border-left: 4px solid #38bdf8;
            color: #f1f5f9; font-size: 16px; font-weight: 500; text-align: center;
            margin-bottom: 40px; box-shadow: 0 4px 20px rgba(0,0,0,0.4);
        }

        div[data-testid="stButton"] > button {
            background-color: rgba(255, 255, 255, 0.95) !important;
            border: 2px solid transparent !important;
            border-radius: 16px !important;
            padding: 60px 20px 40px 20px !important;
            transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1) !important;
            box-shadow: 0 8px 25px rgba(0,0,0,0.4) !important;
            width: 100% !important;
            height: 220px !important;
            position: relative !important;
            overflow: hidden !important; 
        }

        div[data-testid="stButton"] > button p,
        div[data-testid="stButton"] > button div,
        div[data-testid="stButton"] > button span {
            color: #0f172a !important;
            font-size: 22px !important;
            font-weight: 700 !important;
            white-space: pre-wrap !important;
        }

        div[data-testid="stButton"] > button:hover {
            border-color: #38bdf8 !important;
            transform: translateY(-8px) !important;
            box-shadow: 0 20px 40px -10px rgba(56, 189, 248, 0.6) !important;
        }

        div[data-testid="stButton"] > button::before {
            position: absolute;
            top: 0; left: 0; width: 100%; height: auto; min-height: 75px;
            background: linear-gradient(180deg, #1e293b 0%, #0f172a 100%);
            color: #f8fafc !important;
            font-size: 14px; font-weight: 500;
            display: flex; align-items: center; justify-content: center;
            text-align: center; padding: 12px 15px;
            transform: translateY(-100%); 
            transition: transform 0.4s cubic-bezier(0.4, 0, 0.2, 1);
            z-index: 10; line-height: 1.4;
            border-bottom: 2px solid #38bdf8;
            white-space: normal;
        }

        div[data-testid="stColumn"]:nth-child(1) div[data-testid="stButton"] > button::before {
            content: "Experience dead-reckoning fallback, battery conservation, and trigger emergency SOS.";
        }
        div[data-testid="stColumn"]:nth-child(2) div[data-testid="stButton"] > button::before {
            content: "Command tactical map, triage hundreds of victims, and inspect medical/blood telemetry.";
        }
        div[data-testid="stButton"] > button:hover::before { transform: translateY(0); }

        .main-title { text-align: center; font-size: 3.5rem; font-weight: 800; color: #ffffff; margin-bottom: 5px; text-shadow: 0 4px 20px rgba(0,0,0,0.6); }
        .sub-title { text-align: center; font-size: 1.3rem; color: #94a3b8; margin-bottom: 40px; }
    </style>
    """, unsafe_allow_html=True)
    
    spacer_left, center_col, spacer_right = st.columns([1, 3, 1])
    
    with center_col:
        st.markdown("<div class='main-title'>MeowResc</div>", unsafe_allow_html=True)
        st.markdown("<div class='sub-title'>Interactive Disaster Response Simulator</div>", unsafe_allow_html=True)
        
        st.markdown("""
        <div class='prototype-warning'>
            ℹ️ <b>PROTOTYPE NOTICE:</b> This environment simulates hardware telemetry, predictive ML, and dispatch networks during emergencies.
        </div>
        """, unsafe_allow_html=True)

        st.write("<h3 style='text-align: center; margin-bottom: 30px; color: #f8fafc;'>Select Your Simulation Role:</h3>", unsafe_allow_html=True)

        col1, col2 = st.columns(2, gap="large")

        with col1:
            if st.button("📱 Citizen in Distress\n(Victim Simulator)", use_container_width=True):
                set_role("Victim")
                st.rerun()

        with col2:
            if st.button("🚨 Rescue Command\n(First Responder HQ)", use_container_width=True):
                set_role("Rescuer")
                st.rerun()


# =========================================================
# VIEW 2: VICTIM SIMULATOR
# =========================================================
def render_victim_screen():
    is_confirmed = (st.session_state.hazard_level >= 80 or st.session_state.sos_active)
    
    total_steps = 24
    step_angle = (st.session_state.radar_step % total_steps) * (2 * math.pi / total_steps)
    wave_factor = (math.sin(step_angle) + 1.0) / 2.0
    pulse_radius = 450 + (wave_factor * 1150)
    is_expanding = math.cos(step_angle) >= 0

    left_panel, right_panel = st.columns([4, 6], gap="large")

    with left_panel:
        with st.container(border=True):
            top_btn_col, top_title_col = st.columns([1, 2.5])
            with top_btn_col:
                if st.button("← Exit"):
                    set_role(None)
                    st.rerun()
            with top_title_col:
                st.markdown("<h3 style='margin:0; text-align:right;'>MeowApp 🌤️</h3>", unsafe_allow_html=True)
                
            st.markdown("📍 **Current Location:** Wagholi, Pune (MH)")
            st.caption(f"Last Satellite Sync: {datetime.now().strftime('%I:%M:%S %p')}")
            
            # --- PROTOTYPE DISCLAIMER NOTE ---
            st.markdown("""
            <div style="background: rgba(14, 116, 144, 0.18); border-left: 3px solid #06b6d4; border-radius: 6px; padding: 8px 12px; margin: 10px 0; font-size: 11px; color: #cbd5e1; line-height: 1.4;">
                📱 <b>PROTOTYPE MOCK:</b> This desktop interface is an interactive simulation. The actual deployment software is built exclusively as a native mobile application for citizens.
            </div>
            """, unsafe_allow_html=True)
            
            st.divider()
            
            disaster_choice = st.selectbox(
                "⚡ Select Active Hazard Scenario:",
                ["🌊 Flood Threat", "💥 Earthquake / Seismic Surge", "🌀 Cyclone / Tornado"],
                index=["Flood", "Earthquake", "Cyclone"].index(st.session_state.disaster_type),
                key="victim_disaster_choice"
            )
            new_type = disaster_choice.split(" ")[1]
            if new_type != st.session_state.disaster_type:
                st.session_state.disaster_type = new_type
                st.rerun()

            st.markdown("<h5 style='margin-top: 15px;'>Hazard Severity Gauge</h5>", unsafe_allow_html=True)
            lvl = st.session_state.hazard_level
            radius = 50
            circumference = 2 * 3.14159 * radius
            dash_offset = circumference * (1 - (lvl / 100.0))
            
            if lvl < 35:
                gauge_color = "#22c55e"
                status_text = "SAFE / NORMAL"
            elif lvl < 80:
                gauge_color = "#eab308"
                status_text = "STATUS: WATCH"
            else:
                gauge_color = "#ef4444"
                status_text = "STATUS: CRITICAL"

            gauge_html = f"""
            <div style="display: flex; flex-direction: column; align-items: center; justify-content: center; margin: 10px 0;">
                <svg width="170" height="170" viewBox="0 0 120 120">
                    <circle cx="60" cy="60" r="50" fill="none" stroke="#1e293b" stroke-width="12" />
                    <circle cx="60" cy="60" r="50" fill="none" stroke="{gauge_color}" stroke-width="12"
                            stroke-dasharray="{circumference}" stroke-dashoffset="{dash_offset}"
                            stroke-linecap="round" transform="rotate(-90 60 60)" style="transition: all 0.5s ease-in-out;" />
                    <text x="60" y="52" font-family="Cairo" font-weight="800" font-size="22" fill="#ffffff" text-anchor="middle" dominant-baseline="central">{lvl}%</text>
                    <text x="60" y="74" font-family="Mulish" font-weight="700" font-size="8" fill="{gauge_color}" text-anchor="middle">{status_text}</text>
                </svg>
            </div>
            """
            st.markdown(gauge_html, unsafe_allow_html=True)

            if lvl >= 80:
                if st.session_state.disaster_type == "Flood":
                    sensor_info = "⚡ <b>BREAKING POINT TRIGGERED:</b> Riverbank hydro-transducers & Khadakwasla Dam pressure sensors detected critical water discharge."
                elif st.session_state.disaster_type == "Earthquake":
                    sensor_info = "⚡ <b>BREAKING POINT TRIGGERED:</b> MEMS accelerometers detected high peak ground motion (>0.35g)."
                else:
                    sensor_info = "⚡ <b>BREAKING POINT TRIGGERED:</b> Doppler radar detected steep millibar drop (<980 hPa)."

                st.markdown(f"""
                <div style="background: rgba(239, 68, 68, 0.25); border: 1px solid #ef4444; padding: 12px; border-radius: 10px; color: #fca5a5; font-size: 13px; line-height: 1.4; margin-bottom: 15px;">
                    {sensor_info}
                </div>
                """, unsafe_allow_html=True)

            st.divider()
            st.markdown(f"#### 📊 Real-Time {st.session_state.disaster_type} Telemetry")
            if st.session_state.disaster_type == "Flood":
                val1_label, val1_val = "Rainfall Rate", f"{round(2.4 + (lvl * 1.1), 1)} mm/hr"
                val2_label, val2_val = "River Discharge", f"{round(1.2 + (lvl * 0.055), 2)} m"
                val3_label, val3_val = "Barometer", f"{int(1012 - (lvl * 0.3))} hPa"
                val4_label, val4_val = "Soil Saturation", f"{min(100, int(20 + lvl * 0.85))}%"
            elif st.session_state.disaster_type == "Earthquake":
                val1_label, val1_val = "Seismic Magnitude", f"{round(1.5 + (lvl * 0.065), 1)} Richter"
                val2_label, val2_val = "Peak Accel (PGA)", f"{round(0.01 + (lvl * 0.009), 2)} g"
                val3_label, val3_val = "Depth / Focus", "12.4 km"
                val4_label, val4_val = "Primary Wave Delay", f"{max(0.2, round(4.5 - (lvl * 0.04), 1))} sec"
            else:
                val1_label, val1_val = "Sustained Wind", f"{round(15 + (lvl * 1.65), 1)} km/h"
                val2_label, val2_val = "Peak Wind Gust", f"{round(22 + (lvl * 2.1), 1)} km/h"
                val3_label, val3_val = "Central Pressure", f"{int(1012 - (lvl * 0.45))} hPa"
                val4_label, val4_val = "Storm Surge", f"{round(0.2 + (lvl * 0.045), 1)} m"

            t_col1, t_col2 = st.columns(2)
            t_col1.metric(val1_label, val1_val)
            t_col2.metric(val2_label, val2_val)

            t_col3, t_col4 = st.columns(2)
            t_col3.metric(val3_label, val3_val)
            t_col4.metric(val4_label, val4_val)

            st.divider()
            st.markdown("#### ⚙️ Severity Escalation Controls")
            slider_val = st.slider("Scrub Hazard Level (%)", 0, 100, st.session_state.hazard_level, step=5, key="victim_slider")
            if slider_val != st.session_state.hazard_level:
                st.session_state.hazard_level = slider_val
                st.rerun()

            ctrl_col1, ctrl_col2 = st.columns(2)
            with ctrl_col1:
                if st.button("▶️ Animate Surge", key="victim_surge_btn", use_container_width=True):
                    for i in range(st.session_state.hazard_level, 101, 10):
                        st.session_state.hazard_level = i
                        time.sleep(0.12)
                        st.rerun()
            with ctrl_col2:
                if st.button("🔄 Reset to Normal", key="victim_reset_btn", use_container_width=True):
                    st.session_state.hazard_level = 10
                    st.session_state.sos_active = False
                    st.session_state.radar_step = 0
                    st.rerun()

    with right_panel:
        with st.container(border=True):
            sos_col1, sos_col2 = st.columns([3, 1])
            with sos_col1:
                st.markdown("### 🗺️ Live Tracking Map")
            with sos_col2:
                if st.button("🚨 TRIGGER SOS", use_container_width=True, type="primary"):
                    st.session_state.hazard_level = 100
                    st.session_state.sos_active = True
                    st.rerun()

            if is_confirmed:
                st.markdown("""
                <div class='popup-engine popup-dr'>
                    <div style="display:flex; align-items:center; gap: 8px;">
                        <span style="font-size: 16px;">🧭</span>
                        <b style="color: #67e8f9; font-size: 13px; text-transform: uppercase;">Dead Reckoning Engine Activated</b>
                    </div>
                    <div style="font-size: 12px; margin-top: 4px; line-height: 1.4;">
                        Satellite GPS link degraded. System has switched to <b>inertial Dead Reckoning</b> using phone onboard MEMS accelerometers, gyroscope, and step-cadence sensors to maintain real-time position offline.
                    </div>
                </div>
                """, unsafe_allow_html=True)

            if st.session_state.sos_active:
                st.markdown("""
                <div class='popup-engine popup-battery'>
                    <div style="display:flex; align-items:center; gap: 8px;">
                        <span style="font-size: 16px;">🔋</span>
                        <b style="color: #fde047; font-size: 13px; text-transform: uppercase;">Extreme Power Conservation Protocol Engaged</b>
                    </div>
                    <div style="font-size: 12px; margin-top: 4px; line-height: 1.4;">
                        Non-essential OS background tasks, screen refresh rates, and apps have been restricted. Transceiver duty-cycling to ultra-low-power BLE & LoRa beacons to extend battery life up to <b>72 hours</b>.
                    </div>
                </div>
                """, unsafe_allow_html=True)

            if is_confirmed:
                if is_expanding:
                    badge_html = f"<div class='pulse-pill pulse-pill-expanding'>⚠️ THREAT ENVELOPE EXPANDING • Radius: {int(pulse_radius)}m (Surging)</div>"
                else:
                    badge_html = f"<div class='pulse-pill pulse-pill-shrinking'>🔄 THREAT ENVELOPE RECEDING • Radius: {int(pulse_radius)}m (Contracting)</div>"
                st.markdown(badge_html, unsafe_allow_html=True)
            else:
                st.markdown("<div class='pulse-pill' style='background:rgba(34,197,94,0.2); color:#86efac; border:1px solid #22c55e;'>🟢 SECTOR NOMINAL • All environmental sensors in normal range</div>", unsafe_allow_html=True)

            user_lat, user_lon = 18.5808, 73.9787
            d_safe1 = calculate_distance(user_lat, user_lon, 18.5860, 73.9850)
            d_safe2 = calculate_distance(user_lat, user_lon, 18.5750, 73.9690)
            d_fam1 = calculate_distance(user_lat, user_lon, 18.5825, 73.9890)
            d_fam2 = calculate_distance(user_lat, user_lon, 18.5720, 73.9810)

            user_df = pd.DataFrame([{"lat": user_lat, "lon": user_lon, "name": "🔵 You (Dead-Reckoning Position)", "color": [0, 122, 255, 255]}])
            safe_df = pd.DataFrame([
                {"lat": 18.5860, "lon": 73.9850, "name": f"🟢 Wagholi Shelter ({d_safe1} km away)", "color": [34, 197, 94, 255]},
                {"lat": 18.5750, "lon": 73.9690, "name": f"🟢 Lexicon Stadium Shelter ({d_safe2} km away)", "color": [34, 197, 94, 255]}
            ])
            family_df = pd.DataFrame([
                {"lat": 18.5825, "lon": 73.9890, "name": f"🔴 Mom - Safe ({d_fam1} km away)", "color": [239, 68, 68, 255]},
                {"lat": 18.5720, "lon": 73.9810, "name": f"🔴 Brother - Moving ({d_fam2} km away)", "color": [239, 68, 68, 255]}
            ])

            layers = [
                pdk.Layer("ScatterplotLayer", data=user_df, get_position='[lon, lat]', get_fill_color='color', get_radius=130, radius_min_pixels=8, pickable=True),
                pdk.Layer("ScatterplotLayer", data=safe_df, get_position='[lon, lat]', get_fill_color='color', get_radius=160, radius_min_pixels=9, pickable=True),
                pdk.Layer("ScatterplotLayer", data=family_df, get_position='[lon, lat]', get_fill_color='color', get_radius=150, radius_min_pixels=8, pickable=True)
            ]

            # 3-TIER MULTI-RING SHOCKWAVE
            if is_confirmed:
                layers.append(
                    pdk.Layer(
                        "ScatterplotLayer",
                        data=pd.DataFrame([{"lat": user_lat, "lon": user_lon, "radius": pulse_radius}]),
                        get_position='[lon, lat]',
                        get_fill_color=[239, 68, 68, 30],
                        get_line_color=[239, 68, 68, 220],
                        stroked=True,
                        get_radius='radius',
                        line_width_min_pixels=2
                    )
                )
                layers.append(
                    pdk.Layer(
                        "ScatterplotLayer",
                        data=pd.DataFrame([{"lat": user_lat, "lon": user_lon, "radius": pulse_radius * 0.65}]),
                        get_position='[lon, lat]',
                        get_fill_color=[249, 115, 22, 45],
                        get_line_color=[249, 115, 22, 190],
                        stroked=True,
                        get_radius='radius',
                        line_width_min_pixels=2
                    )
                )
                layers.append(
                    pdk.Layer(
                        "ScatterplotLayer",
                        data=pd.DataFrame([{"lat": user_lat, "lon": user_lon, "radius": pulse_radius * 0.35}]),
                        get_position='[lon, lat]',
                        get_fill_color=[220, 38, 38, 85],
                        get_line_color=[220, 38, 38, 255],
                        stroked=True,
                        get_radius='radius',
                        line_width_min_pixels=2
                    )
                )

            view_state = pdk.ViewState(latitude=user_lat, longitude=user_lon, zoom=13, pitch=0)
            st.pydeck_chart(
                pdk.Deck(
                    layers=layers,
                    initial_view_state=view_state,
                    tooltip={"text": "{name}"},
                    map_style=pdk.map_styles.CARTO_DARK
                )
            )
            
            sub_col1, sub_col2 = st.columns([3, 1])
            with sub_col1:
                st.caption("🔵 **Blue:** You | 🟢 **Green:** Safe Spots | 🔴 **Red:** Threat Zone (Active when >=80%)")
            with sub_col2:
                if is_confirmed:
                    st.session_state.auto_pulse = st.toggle("📡 Live Radar", value=st.session_state.auto_pulse)

        with st.container(border=True):
            st.markdown("#### 📡 Multilingual CAP Alert Broadcast")
            lang_tab1, lang_tab2 = st.tabs(["English", "मराठी (Marathi)"])
            
            with lang_tab1:
                if lvl < 35:
                    st.markdown("<div class='alert-box-safe'><b>NDRF Alert:</b> All environmental conditions nominal in Wagholi sector.</div>", unsafe_allow_html=True)
                elif lvl < 80:
                    st.markdown(f"<div class='alert-box-watch'><b>NDRF Tier 1 Warning:</b> Escalating {st.session_state.disaster_type} risk detected. Stay indoors and monitor broadcasts.</div>", unsafe_allow_html=True)
                else:
                    st.markdown(f"<div class='alert-box-disaster'><b>EVACUATION ORDER:</b> Critical {st.session_state.disaster_type} event underway in Wagholi! Move to designated safe zones immediately.</div>", unsafe_allow_html=True)

            with lang_tab2:
                if lvl < 35:
                    st.markdown("<div class='alert-box-safe'><b>एनडीआरएफ सूचना:</b> वाघोली क्षेत्रात सर्व पर्यावरणीय स्थिती सामान्य आहे.</div>", unsafe_allow_html=True)
                elif lvl < 80:
                    st.markdown(f"<div class='alert-box-watch'><b>एनडीआरएफ इशारा:</b> {st.session_state.disaster_type} चा वाढता धोका ओळखला गेला आहे. घरातच राहा.</div>", unsafe_allow_html=True)
                else:
                    st.markdown(f"<div class='alert-box-disaster'><b>तातडीची स्थलांतर आदेश:</b> वाघोलीत गंभीर {st.session_state.disaster_type} आपत्कालीन परिस्थिती! तात्काळ सुरक्षित स्थळी जा.</div>", unsafe_allow_html=True)

    if is_confirmed and st.session_state.auto_pulse:
        st.session_state.radar_step += 1
        time.sleep(0.06)
        st.rerun()


# =========================================================
# VIEW 3: RESCUE COMMAND (FIRST RESPONDER HQ)
# =========================================================
def render_rescuer_screen():
    is_confirmed = (st.session_state.hazard_level >= 80 or st.session_state.sos_active)
    
    if is_confirmed:
        step_angle = (st.session_state.radar_step % 24) * (2 * math.pi / 24)
        wave_factor = (math.sin(step_angle) + 1.0) / 2.0
        disaster_range = 650 + (wave_factor * 1100)
    else:
        disaster_range = 0

    with st.container(border=True):
        c_head1, c_head2, c_head3 = st.columns([1.2, 3.8, 1.5])
        with c_head1:
            if st.button("← Switch Role", use_container_width=True):
                set_role(None)
                st.rerun()
        with c_head2:
            st.markdown("<h2 style='margin:0; text-align:center;'>🚨 NDRF INCIDENT COMMAND HQ</h2>", unsafe_allow_html=True)
            st.markdown("<p style='margin:0; text-align:center; color:#94a3b8; font-size:13px;'>Tactical C4I Terminal • Wagholi Metro Defense Sector 4</p>", unsafe_allow_html=True)
        with c_head3:
            mesh_status = "<b style='color:#ef4444;'>HIGH TRAFFIC</b>" if is_confirmed else "<b style='color:#22c55e;'>ONLINE</b>"
            st.markdown(f"<div style='text-align:right; font-size:12px; color:#cbd5e1;'>MESH STATUS: {mesh_status}<br>SYNC: <b>{datetime.now().strftime('%H:%M:%S IST')}</b></div>", unsafe_allow_html=True)

    dynamic_citizens = []
    base_lat, base_lon = 18.5808, 73.9787

    for c in st.session_state.citizens_dataset:
        c_copy = dict(c)
        if is_confirmed and (c['orig_sos'] or c['dist_km'] < (disaster_range / 1000.0)):
            c_copy['is_sos'] = True
            c_copy['color'] = [239, 68, 68, 230]
            c_copy['status'] = "🚨 CRITICAL SOS: IMMEDIATE EVAC"
        else:
            c_copy['is_sos'] = False
            c_copy['color'] = [56, 189, 248, 160]
            c_copy['status'] = "🟢 Nominal: Civilian Sheltered / Safe"
        dynamic_citizens.append(c_copy)

    total_citizens = len(dynamic_citizens)
    sos_count = sum(1 for c in dynamic_citizens if c['is_sos'])
    critical_medical = sum(1 for c in dynamic_citizens if c['is_sos'] and c['allergies'] != "None")

    kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns(5)
    with kpi1:
        sos_num_color = "#ef4444" if is_confirmed else "#22c55e"
        st.markdown(f"""<div class='hq-stat'><div class='hq-stat-num' style='color:{sos_num_color};'>{sos_count}</div><div class='hq-stat-label'>🚨 SOS Flags Active</div></div>""", unsafe_allow_html=True)
    with kpi2:
        st.markdown(f"""<div class='hq-stat'><div class='hq-stat-num' style='color:#38bdf8;'>{total_citizens}</div><div class='hq-stat-label'>👥 Citizens Monitored</div></div>""", unsafe_allow_html=True)
    with kpi3:
        st.markdown(f"""<div class='hq-stat'><div class='hq-stat-num' style='color:#f59e0b;'>{critical_medical}</div><div class='hq-stat-label'>💉 Medical Alert / Trapped</div></div>""", unsafe_allow_html=True)
    with kpi4:
        st.markdown(f"""<div class='hq-stat'><div class='hq-stat-num' style='color:#22c55e;'>84%</div><div class='hq-stat-label'>🏕️ Safe Shelter Cap</div></div>""", unsafe_allow_html=True)
    with kpi5:
        idx_color = "#ef4444" if is_confirmed else "#38bdf8"
        st.markdown(f"""<div class='hq-stat'><div class='hq-stat-num' style='color:{idx_color};'>{st.session_state.hazard_level}%</div><div class='hq-stat-label'>⚡ Threat Severity Index</div></div>""", unsafe_allow_html=True)

    st.write("")

    hq_left, hq_right = st.columns([4, 6], gap="large")

    with hq_left:
        with st.container(border=True):
            st.markdown("#### ⚙️ Sector Disaster Simulation Controller")
            
            disaster_choice = st.selectbox(
                "⚡ Active Hazard Domain:",
                ["🌊 Flood Threat", "💥 Earthquake / Seismic Surge", "🌀 Cyclone / Tornado"],
                index=["Flood", "Earthquake", "Cyclone"].index(st.session_state.disaster_type),
                key="rescuer_disaster_choice"
            )
            new_type = disaster_choice.split(" ")[1]
            if new_type != st.session_state.disaster_type:
                st.session_state.disaster_type = new_type
                st.rerun()

            slider_val = st.slider("Scrub Regional Hazard Severity (%)", 0, 100, st.session_state.hazard_level, step=5, key="rescuer_slider")
            if slider_val != st.session_state.hazard_level:
                st.session_state.hazard_level = slider_val
                st.rerun()

            ctrl_c1, ctrl_c2 = st.columns(2)
            with ctrl_c1:
                if st.button("▶️ Animate Surge", key="rescuer_surge_btn", use_container_width=True):
                    for i in range(st.session_state.hazard_level, 101, 10):
                        st.session_state.hazard_level = i
                        time.sleep(0.12)
                        st.rerun()
            with ctrl_c2:
                if st.button("🔄 Reset to Normal (Nominal)", key="rescuer_reset_btn", use_container_width=True):
                    st.session_state.hazard_level = 10
                    st.session_state.sos_active = False
                    st.session_state.radar_step = 0
                    st.rerun()

        with st.container(border=True):
            st.markdown(f"#### 📊 Real-Time {st.session_state.disaster_type} Sensor Matrix")
            hl = st.session_state.hazard_level
            cur_dis = st.session_state.disaster_type

            if cur_dis == "Flood":
                m1, m2 = st.columns(2)
                m1.metric("Dam Inflow (Khadakwasla)", f"{int(32000 + hl * 220)} cusecs")
                m2.metric("Nullah Crest Delta", f"+{round(1.4 + hl * 0.04, 2)} m")
                m3, m4 = st.columns(2)
                m3.metric("Rainfall Rate", f"{round(2.4 + hl * 1.1, 1)} mm/hr")
                m4.metric("Soil Saturation", f"{min(100, int(20 + hl * 0.85))}%")
            elif cur_dis == "Earthquake":
                m1, m2 = st.columns(2)
                m1.metric("Epicenter Magnitude", f"{round(1.5 + hl * 0.065, 1)} Mw")
                m2.metric("Peak Ground Accel (PGA)", f"{round(0.01 + hl * 0.009, 3)} g")
                m3, m4 = st.columns(2)
                m3.metric("Hypocenter Depth", "12.4 km")
                m4.metric("Primary Wave Delay", f"{max(0.2, round(4.5 - (hl * 0.04), 1))} sec")
            else:
                m1, m2 = st.columns(2)
                m1.metric("Central Barometer", f"{int(1012 - hl * 0.45)} hPa")
                m2.metric("Sustained Wind", f"{int(15 + hl * 1.65)} km/h")
                m3, m4 = st.columns(2)
                m3.metric("Wind Gust Velocity", f"{int(22 + hl * 2.1)} km/h")
                m4.metric("Storm Surge", f"+{round(0.2 + hl * 0.045, 1)} m")

        with st.container(border=True):
            st.markdown("#### 🚨 Priority Citizen Triage List")
            if is_confirmed:
                filter_sos = st.checkbox("Show Only SOS Distress Signals", value=st.session_state.sos_filter_only)
                st.session_state.sos_filter_only = filter_sos
                display_citizens = [c for c in dynamic_citizens if (not filter_sos or c['is_sos'])]
                display_citizens = sorted(display_citizens, key=lambda x: (not x['is_sos'], x['dist_km']))[:5]
                
                for cit in display_citizens:
                    border_col = "#ef4444" if cit['is_sos'] else "#38bdf8"
                    tag_bg = "rgba(239, 68, 68, 0.25)" if cit['is_sos'] else "rgba(56, 189, 248, 0.2)"
                    st.markdown(f"""
                    <div style="background: rgba(2, 6, 23, 0.65); border-left: 4px solid {border_col}; border-radius: 8px; padding: 10px 12px; margin-bottom: 8px;">
                        <div style="display:flex; justify-content:space-between; align-items:center;">
                            <b style="color:#f8fafc; font-size:13px;">{cit['name']} ({cit['id']})</b>
                            <span style="background:{tag_bg}; color:{border_col}; padding:2px 8px; border-radius:12px; font-size:11px; font-weight:700;">{cit['status'].split(':')[0]}</span>
                        </div>
                        <div style="font-size:12px; color:#cbd5e1; margin-top:4px;">
                            Age: <b>{cit['age']}</b> | Blood: <b style="color:#f43f5e;">{cit['blood_type']}</b> | Dist: <b>{cit['dist_km']} km</b>
                        </div>
                        <div style="font-size:11px; color:#94a3b8; margin-top:2px;">
                            Med/Allergies: <b style="color:#fbbf24;">{cit['allergies']}</b> | Battery: <b>{cit['battery']}</b>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.markdown("<div style='background:rgba(34,197,94,0.15); border:1px solid #22c55e; border-radius:8px; padding:12px; color:#86efac; font-size:13px;'>✅ <b>ALL CITIZENS SAFE:</b> No active SOS signals detected in Wagholi sector. Scrub severity to ≥80% or click 'Animate Surge' to simulate emergency triage.</div>", unsafe_allow_html=True)

    with hq_right:
        with st.container(border=True):
            st.markdown("### 🗺️ Wagholi Tactical Defense Map")
            
            m_col1, m_col2 = st.columns([3, 1])
            with m_col1:
                if is_confirmed:
                    st.markdown(f"<span style='color:#ef4444; font-weight:700;'>🚨 CRITICAL HAZARD ACTIVE:</span> {sos_count} SOS beacons broadcasted in Wagholi.", unsafe_allow_html=True)
                else:
                    st.markdown("<span style='color:#22c55e; font-weight:700;'>🟢 NORMAL PATROL:</span> All 120 civil telemetry transponders nominal.", unsafe_allow_html=True)
            with m_col2:
                if is_confirmed:
                    st.session_state.auto_pulse = st.toggle("📡 Radar Sweep", value=st.session_state.auto_pulse)

            filtered_cits = [c for c in dynamic_citizens if (not (is_confirmed and st.session_state.sos_filter_only) or c['is_sos'])]
            cit_df = pd.DataFrame(filtered_cits)

            layers = []

            if is_confirmed:
                layers.append(pdk.Layer(
                    "ScatterplotLayer",
                    data=pd.DataFrame([{"lat": base_lat, "lon": base_lon, "radius": disaster_range}]),
                    get_position='[lon, lat]',
                    get_fill_color=[239, 68, 68, 35],
                    get_line_color=[239, 68, 68, 240],
                    stroked=True,
                    get_radius='radius',
                    line_width_min_pixels=2
                ))
                layers.append(pdk.Layer(
                    "ScatterplotLayer",
                    data=pd.DataFrame([{"lat": base_lat, "lon": base_lon, "radius": disaster_range * 0.45}]),
                    get_position='[lon, lat]',
                    get_fill_color=[220, 38, 38, 70],
                    get_line_color=[220, 38, 38, 255],
                    stroked=True,
                    get_radius='radius',
                    line_width_min_pixels=2
                ))

            layers.append(pdk.Layer(
                "ScatterplotLayer",
                data=cit_df,
                get_position='[lon, lat]',
                get_fill_color='color',
                get_radius=30,
                radius_min_pixels=3.5,
                radius_max_pixels=7,
                pickable=True
            ))

            safe_df = pd.DataFrame([
                {"lat": 18.5860, "lon": 73.9850, "name": "🟢 Wagholi Central Shelter (Capacity: 84%)", "color": [34, 197, 94, 255]},
                {"lat": 18.5750, "lon": 73.9690, "name": "🟢 Lexicon Stadium Evac Hub (Capacity: 65%)", "color": [34, 197, 94, 255]}
            ])
            layers.append(pdk.Layer(
                "ScatterplotLayer",
                data=safe_df,
                get_position='[lon, lat]',
                get_fill_color='color',
                get_radius=140,
                radius_min_pixels=8,
                pickable=True
            ))

            rescue_fleet = pd.DataFrame([
                {"lat": 18.5830, "lon": 73.9820, "name": "🛡️ NDRF Squad Alpha-1 (Stationed)", "color": [249, 115, 22, 255]},
                {"lat": 18.5790, "lon": 73.9730, "name": "🚤 Rapid Evacuation Boat #3", "color": [6, 182, 212, 255]},
                {"lat": 18.5710, "lon": 73.9820, "name": "🚑 Trauma Ambulance Unit #02", "color": [236, 72, 153, 255]}
            ])
            layers.append(pdk.Layer(
                "ScatterplotLayer",
                data=rescue_fleet,
                get_position='[lon, lat]',
                get_fill_color='color',
                get_radius=150,
                radius_min_pixels=8,
                pickable=True
            ))

            tooltip_cfg = {
                "html": """
                <div style="background:#0f172a; border:1px solid #38bdf8; border-radius:8px; padding:10px; font-family:sans-serif; color:#ffffff; min-width:180px;">
                    <b style="font-size:13px; color:#38bdf8;">{name}</b><br/>
                    <span style="font-size:11px; color:#fca5a5; font-weight:700;">{status}</span>
                    <hr style="margin:6px 0; border:0; border-top:1px solid rgba(255,255,255,0.15);" />
                    <div style="font-size:11px; line-height:1.5;">
                        🩸 Blood Type: <b>{blood_type}</b><br/>
                        🎂 Age: <b>{age}</b> yrs<br/>
                        ⚠️ Allergies/Meds: <b style="color:#fbbf24;">{allergies}</b><br/>
                        🔋 Device Battery: <b>{battery}</b><br/>
                        📍 Distance: <b>{dist_km} km</b>
                    </div>
                </div>
                """,
                "style": {"backgroundColor": "transparent", "padding": "0"}
            }

            hq_view = pdk.ViewState(latitude=base_lat, longitude=base_lon, zoom=13.2, pitch=25)
            
            st.pydeck_chart(
                pdk.Deck(
                    layers=layers,
                    initial_view_state=hq_view,
                    tooltip=tooltip_cfg,
                    map_style=pdk.map_styles.CARTO_DARK
                )
            )

            if is_confirmed:
                st.caption("🔴 **Red Dots:** Critical SOS Victims (Hover for Blood/Medical) | 🟢 **Green:** Shelters | 🟠 **Pins:** Rescue Fleet")
            else:
                st.caption("🔵 **Cyan Dots:** Safe Civilians (All Normal) | 🟢 **Green:** Shelters | 🟠 **Pins:** Patrol Units")

            d_btn1, d_btn2, d_btn3 = st.columns(3)
            with d_btn1:
                if st.button("🚨 Scramble All NDRF Teams", use_container_width=True):
                    st.toast("⚡ NDRF Units 1-4 deployed to Wagholi hotspots!")
            with d_btn2:
                if st.button("📡 Broadcast Sector Alert", use_container_width=True):
                    st.toast("⚠️ Emergency Alert signal beamed over Mesh Nodes.")
            with d_btn3:
                if st.button("🚁 Launch Drone Recon", use_container_width=True):
                    st.toast("Recon Drone #1 airborne over Wagholi-Bakori axis.")

    if is_confirmed and st.session_state.auto_pulse:
        st.session_state.radar_step += 1
        time.sleep(0.06)
        st.rerun()


# =========================================================
# APPLICATION ROUTER
# =========================================================
if st.session_state.role == "Victim":
    render_victim_screen()
elif st.session_state.role == "Rescuer":
    render_rescuer_screen()
else:
    render_landing_page()