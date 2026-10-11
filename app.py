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
                        "break_hours": ["12 PM"], # Defaults
                        "training_hours": ["7 AM"],
                        "avail_hours": ["9 AM", "1 PM", "3 PM", "4 PM"]
                    }
                    supabase.table("staff_profiles").insert(data).execute()
                    st.success("Account created! You can now log in.")
                except Exception as e:
                    st.error(f"Error details: {e}")
            else:
                st.warning("Please fill in both fields.")
    st.stop()

# ==========================================
# SIDEBAR - ACCOUNT SETTINGS
# ==========================================
with st.sidebar:
    st.write(f"👤 **{st.session_state.username}**")
    
    with st.expander("⚙️ Account Settings"):
        new_pwd = st.text_input("Change Password", type="password")
        if st.button("Update Password"):
            if new_pwd:
                new_hash = hash_password(new_pwd)
                supabase.table("staff_profiles").update({"password_hash": new_hash}).eq("username", st.session_state.username).execute()
                st.success("Password Updated!")
            else:
                st.warning("Enter a new password.")
                
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
    .tz-table tbody tr:focus-within td:not(.tz-row-header) { background-color: rgba(255, 234, 0, 0.3) !important; }
    .tz-table td:not(.tz-row-header):focus { background-color: rgba(255, 234, 0, 0.95) !important; color: #121212 !important; box-shadow: inset 0 0 0 3px #FFD600, 0 0 20px rgba(255, 234, 0, 0.9); z-index: 6; outline: none; }
    .tz-table td:not(.tz-row-header):focus * { color: #121212 !important; font-weight: bold; }
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
    st.markdown("🖱️ **Interactive**: **Hover** for Blue Crosshair | **Click** a cell to lock!")

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
        st.success("Settings Saved! The email template has been updated automatically.")

    # Map selected options back to integers
    BREAK_HOURS = [hour_opts[k] for k in break_hours_input]
    TRAINING_HOURS = [hour_opts[k] for k in training_hours_input]
    AVAIL_HOURS = sorted([hour_opts[k] for k in avail_hours_input])

    st.divider()

    st.markdown("##### 2. Dashboard View Options")
    col1, col2, col3 = st.columns([1.5, 1, 1.5])
    with col1:
        selected_tzs = st.multiselect("Select Time Zones:", options=list(TZ_OPTIONS.keys()), default=["Pacific Time (PT)", "Kuala Lumpur (MYT)", "Mountain Time (MT)", "Central Time (CT)", "Eastern Time (ET)"])
    with col2:
        time_format = st.radio("Time Format:", ["12-Hour (AM/PM)", "24-Hour"])
    with col3:
        meeting_options = {f"{h%12 or 12} {'AM' if h < 12 else 'PM'} PST": h for h in range(w_start, w_end + 1)}
        booked_hours = st.multiselect("🔴 Mark Booked Zoom Meetings (PST):", options=list(meeting_options.keys()))
        booked_h_vals = [meeting_options[k] for k in booked_hours]

base_tz = pytz.timezone("America/Los_Angeles")
now_utc = datetime.utcnow().replace(tzinfo=pytz.utc)
current_live_time_pst = now_utc.astimezone(base_tz)

with dashboard_placeholder:
    if not selected_tzs:
        st.info("Please select at least one time zone.")
    else:
        start_of_day = current_live_time_pst.replace(hour=0, minute=0, second=0, microsecond=0)
        html = '<div class="tz-container"><table class="tz-table"><tr><th class="tz-row-header">Time (Hour)</th>'
        for h in range(24):
            display_time = start_of_day + timedelta(hours=h)
            h_str = display_time.strftime("%I %p").lstrip("0").lower() if "12" in time_format else display_time.strftime("%H:00")
            cell_class = get_cell_classes(h, booked_h_vals, AVAIL_HOURS, BREAK_HOURS, TRAINING_HOURS, w_start, w_end)
            html += f'<th class="{cell_class}">{h_str}</th>'
        html += '</tr>'

        for tz_name in selected_tzs:
            tz_obj = pytz.timezone(TZ_OPTIONS[tz_name])
            live_tz_time = now_utc.astimezone(tz_obj)
            live_str = live_tz_time.strftime("%I:%M %p").lstrip("0").lower() if "12" in time_format else live_tz_time.strftime("%H:%M")
            offset_diff = (start_of_day.astimezone(tz_obj).utcoffset().total_seconds() - start_of_day.utcoffset().total_seconds()) / 3600
            offset_str = f"{int(offset_diff)}h" if offset_diff < 0 else f"+{int(offset_diff)}h"
            if offset_diff == 0: offset_str = "Base"

            html += f'<tr><td class="tz-row-header">{tz_name} <br><span class="sub-text">({offset_str}) • Live: {live_str}</span></td>'
            for h in range(24):
                base_time = start_of_day + timedelta(hours=h)
                tz_time = base_time.astimezone(tz_obj)
                bg_class = "tz-day" if 7 <= tz_time.hour < 19 else "tz-night"
                cell_class = f"{bg_class} {get_cell_classes(h, booked_h_vals, AVAIL_HOURS, BREAK_HOURS, TRAINING_HOURS, w_start, w_end)}"
                t_str = tz_time.strftime("%I %p").lstrip("0").lower() if "12" in time_format else tz_time.strftime("%H:00")
                html += f'<td class="{cell_class}" tabindex="0">{t_str}<br><span class="sub-text">{tz_time.strftime("%b %d")}</span></td>'
            html += '</tr>'
        html += '</table></div>'
        st.markdown(html, unsafe_allow_html=True)

st.divider()

# ==========================================
# EMAIL TEMPLATE ASSISTANT (DYNAMIC)
# ==========================================
st.header("✉️ Email Template Assistant")
st.markdown("Your selected **Available Times** from the controls above are automatically generated as columns below.")

with st.container(border=True):
    target_tz_select = st.selectbox("Client Time Zone:", options=list(TZ_OPTIONS.keys()), index=2)

    st.markdown("**Meeting Dates:**")
    d_col1, d_col2, d_col3 = st.columns(3)
    with d_col1: date1 = st.date_input("Day 1", value=datetime.today().date())
    with d_col2: date2 = st.date_input("Day 2", value=date1 + timedelta(days=1))
    with d_col3: date3 = st.date_input("Day 3", value=date1 + timedelta(days=2))
    
    # Generate chopping options dynamically based on Available Hours
    slot_options = []
    for d in [date1, date2, date3]:
        date_str = d.strftime('%m/%d/%Y')
        for i in range(len(AVAIL_HOURS)):
            slot_options.append(f"{date_str} - Slot {i+1}")
            
    booked_template_slots = st.multiselect("Chop Unavailable Slots (Mark as Booked):", options=slot_options)

st.subheader("📋 Output (Ready to Copy)")

target_tz_obj = pytz.timezone(TZ_OPTIONS[target_tz_select])
tz_abbr = target_tz_select.split("(")[-1].replace(")", "")

def get_slot_time_str(date_val, start_hour):
    """Calculates exactly 1 hour block for the target timezone"""
    start_dt = base_tz.localize(datetime(date_val.year, date_val.month, date_val.day, start_hour, 0))
    end_dt = base_tz.localize(datetime(date_val.year, date_val.month, date_val.day, start_hour + 1, 0))
    return f"{start_dt.astimezone(target_tz_obj).strftime('%I:%M %p').lstrip('0')} - {end_dt.astimezone(target_tz_obj).strftime('%I:%M %p').lstrip('0')}"

# Dynamically build table headers based on length of AVAIL_HOURS
header_html = "".join([f'<th style="border: 1px solid #e0e0e0; padding: 8px; text-align: center; color: #212121;">Slot {i+1}</th>' for i in range(len(AVAIL_HOURS))])

# Dynamically build table rows based on length of AVAIL_HOURS
rows_html = ""
for d in [date1, date2, date3]:
    date_formatted = d.strftime('%m/%d/%Y')
    day_name = d.strftime('%A')
    
    row_cells = ""
    for i, h in enumerate(AVAIL_HOURS):
        slot_key = f"{date_formatted} - Slot {i+1}"
        if slot_key in booked_template_slots:
            row_cells += '<td style="border: 1px solid #e0e0e0; padding: 8px; text-align: center; color: #2e7d32;"><i><b>Booked</b></i></td>'
        else:
            time_str = get_slot_time_str(d, h)
            row_cells += f'<td style="border: 1px solid #e0e0e0; padding: 8px; text-align: center; color: #212121;">{time_str}</td>'
            
    rows_html += f"""<tr>
<td style="border: 1px solid #e0e0e0; padding: 8px; text-align: center; color: #212121;">{date_formatted}</td>
<td style="border: 1px solid #e0e0e0; padding: 8px; text-align: center; color: #212121;">{day_name}</td>
{row_cells}
<td style="border: 1px solid #e0e0e0; padding: 8px; text-align: center; color: #212121;">{tz_abbr}</td>
</tr>"""

email_html = f"""<div style="font-family: sans-serif; font-size: 14px; color: #212121; line-height: 1.5; background-color: #ffffff; padding: 20px; border-radius: 8px; border: 2px solid #2196F3;">
<b>Following Up</b><br><br>
1. Would you prefer us to call or continue over email?<br>
2. If yes, is <b>[PHONE NUMBER], {tz_abbr}</b> and <b>[EMAIL]</b> the best way to reach you?<br>
3. We would like to do a screenshare, my current availability is shown below :<br><br>
<table style="border-collapse: collapse; width: 100%; max-width: 800px; border: 1px solid #e0e0e0;">
<tr style="background-color: #f8f9fa;">
<th style="border: 1px solid #e0e0e0; padding: 8px; text-align: center; color: #212121;">Date</th>
<th style="border: 1px solid #e0e0e0; padding: 8px; text-align: center; color: #212121;">Day</th>
{header_html}
<th style="border: 1px solid #e0e0e0; padding: 8px; text-align: center; color: #212121;">Time Zone</th>
</tr>
{rows_html}
</table><br><br>
<b>Action Plan</b><br>
<ul style="margin-top: 8px;">
<li>Please reply with your preferred meeting time and the requested information above.</li>
<li>If the above isn't possible, let me know your general availability for the week and I'll try to accommodate my schedule to yours.</li>
</ul>
<br>
You can reach us by replying to this email or calling [SUPPORT PHONE] (provide the case number <b>[CASE NUMBER]</b>). We're available from 5.00 A.M. to 5.00 P.M. (Pacific Time), Monday through Friday.
</div>"""

if len(AVAIL_HOURS) == 0:
    st.warning("⚠️ No Available Times selected. Add times in the controls above to generate the email table.")
else:
    st.markdown(email_html, unsafe_allow_html=True)
