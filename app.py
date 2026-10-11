import streamlit as st
from datetime import datetime, timedelta
import pytz
from supabase import create_client, Client
import bcrypt

st.set_page_config(page_title="Meeting Planner & Email Assist", page_icon="🌍", layout="wide")

# ==========================================
# DATABASE INITIALIZATION
# ==========================================
@st.cache_resource
def init_connection():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

supabase: Client = init_connection()

# ==========================================
# AUTHENTICATION & PROFILE MANAGEMENT
# ==========================================
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "username" not in st.session_state:
    st.session_state.username = None
if "user_settings" not in st.session_state:
    st.session_state.user_settings = {}

def hash_password(password):
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def check_password(password, hashed):
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

if not st.session_state.authenticated:
    st.title("🔒 Staff Login")
    tab1, tab2 = st.tabs(["Login", "Create Account"])
    
    with tab1:
        log_user = st.text_input("Username", key="log_user")
        log_pwd = st.text_input("Password", type="password", key="log_pwd")
        if st.button("Login"):
            try:
                response = supabase.table("staff_profiles").select("*").eq("username", log_user).execute()
                if len(response.data) > 0:
                    user_data = response.data[0]
                    if check_password(log_pwd, user_data['password_hash']):
                        st.session_state.authenticated = True
                        st.session_state.username = user_data['username']
                        st.session_state.user_settings = {
                            "w_start": user_data.get('w_start', 7),
                            "w_end": user_data.get('w_end', 16),
                            "break_hours": user_data.get('break_hours', []),
                            "training_hours": user_data.get('training_hours', []),
                            "avail_hours": user_data.get('avail_hours', [])
                        }
                        st.rerun()
                    else:
                        st.error("Incorrect Password")
                else:
                    st.error("User not found")
            except Exception as e:
                st.error(f"Database error: {e}")

    with tab2:
        reg_user = st.text_input("Choose Username", key="reg_user")
        reg_pwd = st.text_input("Choose Password", type="password", key="reg_pwd")
        if st.button("Create Account"):
            if reg_user and reg_pwd:
                try:
                    hashed_pw = hash_password(reg_pwd)
                    data = {
                        "username": reg_user,
                        "password_hash": hashed_pw,
                        "break_hours": ["12 PM"],
                        "training_hours": ["7 AM"],
                        "avail_hours": ["9 AM", "1 PM", "3 PM"]
                    }
                    supabase.table("staff_profiles").insert(data).execute()
                    st.success("Account created! You can now log in.")
                except Exception as e:
                    st.error("Username might already exist or database error occurred.")
            else:
                st.warning("Please fill in both fields.")
    st.stop()

# Sidebar User Info & Logout
with st.sidebar:
    st.write(f"👤 Logged in as: **{st.session_state.username}**")
    if st.button("Logout"):
        st.session_state.authenticated = False
        st.session_state.username = None
        st.rerun()

# ==========================================
# CUSTOM CSS
# ==========================================
st.markdown("""
<style>
    .tz-container { overflow: hidden; position: relative; margin-bottom: 20px; padding-bottom: 15px; border-radius: 8px; }
    .tz-table { width: 100%; border-collapse: collapse; text-align: center; font-family: sans-serif; min-width: 1300px; }
    .tz-table th, .tz-table td { border: 1px solid rgba(150, 150, 150, 0.2); padding: 8px 4px; position: relative; transition: background-color 0.1s ease; }
    .tz-row-header { text-align: left; font-weight: bold; width: 180px; padding-left: 12px !important; position: sticky; left: 0; z-index: 10 !important; background-color: #262730 !important; border-right: 2px solid rgba(150, 150, 150, 0.5) !important; }
    .tz-night { background-color: rgba(128, 128, 128, 0.1); opacity: 0.8; }
    .tz-day { background-color: transparent; }
    .tz-working { background-color: rgba(224, 64, 251, 0.25) !important; }
    .tz-break { background-color: rgba(255, 235, 59, 0.25) !important; color: #FBC02D; font-weight: bold; }
    .tz-break-left { border-left: 2px solid #FBC02D !important; }
    .tz-break-right { border-right: 2px solid #FBC02D !important; }
    .tz-training { background-color: rgba(3, 169, 244, 0.3) !important; color: #4FC3F7; font-weight: bold; }
    .tz-training-left { border-left: 2px solid #29B6F6 !important; }
    .tz-training-right { border-right: 2px solid #29B6F6 !important; }
    .tz-booked { background-color: rgba(244, 67, 54, 0.5) !important; color: #ffcdd2; font-weight: bold; }
    .tz-booked-left { border-left: 2px solid #F44336 !important; }
    .tz-booked-right { border-right: 2px solid #F44336 !important; }
    .tz-avail { background-color: rgba(40, 167, 69, 0.3) !important; color: #4CAF50; font-weight: bold; }
    .tz-avail-left { border-left: 2px solid #28a745 !important; }
    .tz-avail-right { border-right: 2px solid #28a745 !important; }
    .sub-text { font-size: 11px; opacity: 0.7; display: block; margin-top: 4px; font-weight: normal;}
    .tz-table tbody tr:hover td:not(.tz-row-header) { background-color: rgba(0, 229, 255, 0.25) !important; }
    .tz-table td:not(.tz-row-header):hover { background-color: rgba(0, 229, 255, 0.9) !important; color: #121212 !important; box-shadow: inset 0 0 0 3px #00B8D4, 0 0 15px rgba(0, 229, 255, 0.8); cursor: crosshair; z-index: 5; }
    .tz-table td:not(.tz-row-header):hover *, .tz-table th:not(.tz-row-header):hover * { color: #121212 !important; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

TZ_OPTIONS = {
    "Pacific Time (PT)": "America/Los_Angeles", "Kuala Lumpur (MYT)": "Asia/Kuala_Lumpur",
    "Mountain Time (MT)": "America/Denver", "Central Time (CT)": "America/Chicago",
    "Eastern Time (ET)": "America/New_York", "Alaska Time (AKT)": "America/Anchorage",
    "Hawaii Time (HT)": "Pacific/Honolulu", "London (UK)": "Europe/London",
    "Sydney (AEST)": "Australia/Sydney", "UTC / GMT": "UTC"
}

def get_cell_classes(h, booked_h, avail_h, break_h, train_h, w_start, w_end):
    classes = []
    if h in booked_h:
        classes.append("tz-booked")
        if h - 1 not in booked_h: classes.append("tz-booked-left")
        if h + 1 not in booked_h: classes.append("tz-booked-right")
    elif h in break_h:
        classes.append("tz-break")
        if h - 1 not in break_h: classes.append("tz-break-left")
        if h + 1 not in break_h: classes.append("tz-break-right")
    elif h in train_h:
        classes.append("tz-training")
        if h - 1 not in train_h: classes.append("tz-training-left")
        if h + 1 not in train_h: classes.append("tz-training-right")
    elif h in avail_h:
        classes.append("tz-avail")
        if h - 1 not in avail_h: classes.append("tz-avail-left")
        if h + 1 not in avail_h: classes.append("tz-avail-right")
    elif w_start <= h <= w_end:
        classes.append("tz-working")
    return " ".join(classes)

st.title("🌍 Global Time Zone Dashboard")

st.markdown("**Legend:**")
l_col1, l_col2 = st.columns(2)
with l_col1:
    st.markdown("🟣 **Purple**: Working Hours")
    st.markdown("🟢 **Green**: Available for Meetings")
    st.markdown("🟡 **Yellow**: Break")
with l_col2:
    st.markdown("🔵 **Light Blue**: Training")
    st.markdown("🔴 **Red**: Booked Meetings")
    st.markdown("🖱️ **Interactive**: Hover/Click cells!")

dashboard_placeholder = st.container()
st.divider()

# ==========================================
# PLANNER & SCHEDULE CONTROLS
# ==========================================
st.subheader("⚙️ Planner & Schedule Controls")

with st.container(border=True):
    st.markdown(f"##### 1. {st.session_state.username}'s Schedule Configuration (Base: PST)")
    hour_opts = {f"{h%12 or 12} {'AM' if h < 12 else 'PM'}": h for h in range(24)}
    
    prefs = st.session_state.user_settings
    
    sc1, sc2 = st.columns(2)
    with sc1:
        w_start, w_end = st.slider("General Working Hours (PST)", 0, 23, (prefs['w_start'], prefs['w_end']), format="%d:00")
    with sc2:
        break_hours_input = st.multiselect("🟡 Break Time", options=list(hour_opts.keys()), default=prefs['break_hours'])
    
    sc3, sc4 = st.columns(2)
    with sc3:
        training_hours_input = st.multiselect("🔵 Training Time", options=list(hour_opts.keys()), default=prefs['training_hours'])
    with sc4:
        avail_hours_input = st.multiselect("🟢 Available Time", options=list(hour_opts.keys()), default=prefs['avail_hours'])
    
    if st.button("💾 Save My Settings"):
        new_settings = {
            "w_start": w_start, "w_end": w_end,
            "break_hours": break_hours_input,
            "training_hours": training_hours_input,
            "avail_hours": avail_hours_input
        }
        supabase.table("staff_profiles").update(new_settings).eq("username", st.session_state.username).execute()
        st.session_state.user_settings = new_settings
        st.success("Settings Saved!")

    BREAK_HOURS = [hour_opts[k] for k in break_hours_input]
    TRAINING_HOURS = [hour_opts[k] for k in training_hours_input]
    AVAIL_HOURS = sorted
