import streamlit as st
import requests
import pandas as pd
import plotly.graph_objects as go
from google.cloud import firestore
from streamlit_autorefresh import st_autorefresh
import pytz

# =========================================================
# CONFIGURATION
# =========================================================
FIREBASE_API_KEY = "paste firebase api key here"
REFRESH_INTERVAL_MS = 3000  # 3 seconds

# =========================================================
# PAGE CONFIG
# =========================================================
st.set_page_config(
    page_title="Smart Air Quality Dashboard",
    page_icon="🌫️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =========================================================
# AUTO REFRESH
# =========================================================
st_autorefresh(interval=REFRESH_INTERVAL_MS, key="air_refresh")

# =========================================================
# FIRESTORE INIT
# =========================================================
db = firestore.Client()

# =========================================================
# SESSION STATE
# =========================================================
if "user" not in st.session_state:
    st.session_state.user = None

# =========================================================
# HELPER FUNCTIONS
# =========================================================
def get_status_color(level):
    if level == "Good":
        return "#28a745"
    elif level == "Moderate":
        return "#ffc107"
    elif level == "Unhealthy":
        return "#ff6b6b"
    else:
        return "#8b0000"

def get_status_icon(level):
    if level == "Good":
        return "🟢"
    elif level == "Moderate":
        return "🟡"
    elif level == "Unhealthy":
        return "🔴"
    else:
        return "☠️"

# =========================================================
# ADMIN CHECK
# =========================================================
def is_admin(uid):
    doc = db.collection("users").document(uid).get()
    return doc.exists and doc.to_dict().get("role") == "admin"

# =========================================================
# LOGIN PAGE
# =========================================================
if st.session_state.user is None:
    st.title("Login")
    st.caption("Smart Air Quality Monitoring System")

    email = st.text_input("Email")
    password = st.text_input("Password", type="password")

    if st.button("Login", use_container_width=True):
        payload = {
            "email": email,
            "password": password,
            "returnSecureToken": True
        }

        r = requests.post(
            f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={FIREBASE_API_KEY}",
            json=payload
        )

        if r.status_code == 200:
            data = r.json()
            uid = data["localId"]

            if not is_admin(uid):
                st.error("Access denied.")
                st.stop()

            st.session_state.user = {"email": email, "uid": uid}
            st.success("Login successful")
            st.rerun()
        else:
            st.error("Invalid email or password")

    st.stop()

# =========================================================
# SIDEBAR
# =========================================================
st.sidebar.success(f"Logged in as:\n{st.session_state.user['email']}")

if st.sidebar.button("Logout"):
    st.session_state.user = None
    st.rerun()

# =========================================================
# LOAD DATA
# =========================================================
docs = (
    db.collection("air_quality")
    .order_by("timestamp", direction=firestore.Query.DESCENDING)
    .limit(100)
    .stream()
)

data = [d.to_dict() for d in docs]

if not data:
    st.warning("No air quality data available yet.")
    st.stop()

df = pd.DataFrame(data)
df["timestamp"] = pd.to_datetime(df["timestamp"])

# =========================================================
# SIDEBAR - DATE RANGE FILTER
# =========================================================
st.sidebar.markdown("### Filter by Date Range")

min_date = df["timestamp"].min().date()
max_date = df["timestamp"].max().date()

date_range = st.sidebar.date_input(
    "Select date range:",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date
)

if len(date_range) == 2:
    start_date, end_date = date_range
    df_filtered = df[(df["timestamp"].dt.date >= start_date) & (df["timestamp"].dt.date <= end_date)].copy()
else:
    df_filtered = df.copy()


# =========================================================
# LATEST DATA
# =========================================================
latest = df.iloc[0]

gas = int(latest.get("gas", 0))
fan = latest.get("fan", "OFF")
led = latest.get("led", "OFF")
level = latest.get("level", "Unknown")
timestamp = latest.get("timestamp")

status_color = get_status_color(level)
status_icon = get_status_icon(level)

# =========================================================
# HEADER
# =========================================================
st.title("🌫️ Smart Air Quality Monitoring Dashboard")

# =========================================================
# KPI METRICS
# =========================================================
col1, col2, col3, col4 = st.columns(4)

col1.metric("Air Quality Level", level)
col2.metric("Gas Value", gas)
col3.metric("Fan Status", fan)
col4.metric("LED Status", led)

# =========================================================
# ALERT MESSAGE
# =========================================================
if level == "Good":
    st.success("✅ Good air quality.")
elif level == "Moderate":
    st.info("⚠️ Moderate air quality detected.")
elif level == "Unhealthy":
    st.warning("🚨 Unhealthy air detected! Take action.")
else:
    st.error("☠️ Hazardous air quality! Immediate action required.")

# =========================================================
# ANALYTICS & TRENDS
# =========================================================
st.markdown("## Analytics & Trends")

tab1, tab2 = st.tabs(["Gas Trend", "Historical Records"])

malaysia_tz = pytz.timezone("Asia/Kuala_Lumpur")

# ---------- TREND TAB ----------
with tab1:
    df_plot = df_filtered.copy()
    malaysia_tz = pytz.timezone("Asia/Kuala_Lumpur")
    
    # Check if already timezone-aware
    if df_plot["timestamp"].dt.tz is None:
        df_plot["timestamp"] = df_plot["timestamp"].dt.tz_localize('UTC').dt.tz_convert(malaysia_tz)
    else:
        df_plot["timestamp"] = df_plot["timestamp"].dt.tz_convert(malaysia_tz)

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=df_plot["timestamp"],
        y=df_plot["gas"],
        mode="lines+markers",
        name="Gas Value",
        line=dict(color="#0066cc", width=3),
        marker=dict(size=6),
        fill="tozeroy",
        fillcolor="rgba(0, 102, 204, 0.2)"
    ))

    # Threshold reference lines (must match ESP32 logic)
    fig.add_hline(y=1200, line_dash="dash", line_color="green", annotation_text="Good")
    fig.add_hline(y=1500, line_dash="dash", line_color="orange", annotation_text="Moderate")
    fig.add_hline(y=1800, line_dash="dash", line_color="darkred", annotation_text="Unhealthy")

    fig.update_layout(
        title="Gas Value Over Time",
        xaxis_title="Time ",
        yaxis_title="Gas Value",
        height=400,
        template="plotly_white",
        hovermode="x unified"
    )

    st.plotly_chart(fig, use_container_width=True)

# ---------- RECORDS TAB ----------
with tab2:
    table_df = df_filtered[["timestamp", "gas", "level", "fan", "led"]].copy()
    malaysia_tz = pytz.timezone("Asia/Kuala_Lumpur")
    
    # Check if already timezone-aware
    if table_df["timestamp"].dt.tz is None:
        table_df["timestamp"] = table_df["timestamp"].dt.tz_localize('UTC').dt.tz_convert(malaysia_tz)
    else:
        table_df["timestamp"] = table_df["timestamp"].dt.tz_convert(malaysia_tz)
    
    table_df["timestamp"] = table_df["timestamp"].dt.strftime("%Y-%m-%d %H:%M:%S")

    st.dataframe(
        table_df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "timestamp": st.column_config.TextColumn("Timestamp", width="medium"),
            "gas": st.column_config.NumberColumn("Gas", format="%d"),
            "level": st.column_config.TextColumn("Air Quality"),
            "fan": st.column_config.TextColumn("Fan"),
            "led": st.column_config.TextColumn("LED")
        }
    )

# =========================================================
# INSIGHTS
# =========================================================
st.markdown("---")
st.markdown("## Key Insights")

col_i1, col_i2, col_i3, col_i4, col_i5 = st.columns(5)

# Calculate insights
fan_on_count = (df_filtered['fan'] == 'ON').sum()
fan_percentage = (fan_on_count / len(df_filtered)) * 100 if len(df_filtered) > 0 else 0

good_count = (df_filtered['level'] == 'Good').sum()
good_percentage = (good_count / len(df_filtered)) * 100 if len(df_filtered) > 0 else 0

moderate_count = (df_filtered['level'] == 'Moderate').sum()
moderate_percentage = (moderate_count / len(df_filtered)) * 100 if len(df_filtered) > 0 else 0

unhealthy_count = (df_filtered['level'] == 'Unhealthy').sum()
unhealthy_percentage = (unhealthy_count / len(df_filtered)) * 100 if len(df_filtered) > 0 else 0

hazardous_count = (df_filtered['level'] == 'Hazardous').sum()
hazardous_percentage = (hazardous_count / len(df_filtered)) * 100 if len(df_filtered) > 0 else 0

with col_i1:
    st.metric("Fan Activation", f"{fan_percentage:.1f}%", f"Active {fan_on_count} times")

with col_i2:
    st.metric("Good Air", f"{good_percentage:.1f}%", f"{good_count} readings")

with col_i3:
    st.metric("Moderate Air", f"{moderate_percentage:.1f}%", f"{moderate_count} readings")

with col_i4:
    st.metric("Unhealthy Air", f"{unhealthy_percentage:.1f}%", f"{unhealthy_count} readings")

with col_i5:
    st.metric("Hazardous Air", f"{hazardous_percentage:.1f}%", f"{hazardous_count} readings")
