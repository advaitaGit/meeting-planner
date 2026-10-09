import streamlit as st
from datetime import datetime, timedelta
import pytz

st.set_page_config(page_title="Meeting Planner & Email Assist", page_icon="🌍", layout="wide")

# ==========================================
# CUSTOM CSS FOR CROSSHAIR HOVER, CLICK-TO-STICK & GRID
# ==========================================
st.markdown("""
<style>
    /* Table Container - overflow:hidden clips the vertical columns */
    .tz-container { 
        overflow: hidden; 
        position: relative;
        margin-bottom: 20px; 
        padding-bottom: 15px; 
        border-radius: 8px;
    }
    
    .tz-table { 
        width: 100%; 
        border-collapse: collapse; 
        text-align: center; 
        font-family: sans-serif; 
        min-width: 1300px; 
    }
    
    .tz-table th, .tz-table td { 
        border: 1px solid rgba(150, 150, 150, 0.2); 
        padding: 8px 4px; 
        position: relative; 
        transition: background-color 0.1s ease;
    }
    
    /* Sticky Row Header */
    .tz-row-header { 
        text-align: left; 
        font-weight: bold; 
        width: 180px; 
        padding-left: 12px !important; 
        position: sticky; 
        left: 0; 
        z-index: 10 !important; 
        background-color: #262730 !important; 
        border-right: 2px solid rgba(150, 150, 150, 0.5) !important;
    }
    
    /* --- BASE CELL COLORS --- */
    .tz-night { background-color: rgba(128, 128, 128, 0.1); opacity: 0.8; }
    .tz-day { background-color: transparent; }
    
    /* PST Working Hours (7 AM - 5 PM) - Brighter Neon Purple */
    .tz-working { background-color: rgba(224, 64, 251, 0.25) !important; }

    /* Break Time (12 PM) - Yellow */
    .tz-break { background-color: rgba(255, 235, 59, 0.25) !important; color: #FBC02D; font-weight: bold; }
    .tz-break-left { border-left: 2px solid #FBC02D !important; }
    .tz-break-right { border-right: 2px solid #FBC02D !important; }

    /* Training Time (7 AM - 8 AM) - Light Blue */
    .tz-training { background-color: rgba(3, 169, 244, 0.3) !important; color: #4FC3F7; font-weight: bold; }
    .tz-training-left { border-left: 2px solid #29B6F6 !important; }
    .tz-training-right { border-right: 2px solid #29B6F6 !important; }

    /* Booked Meeting (Zoom) - Coral/Red */
    .tz-booked { background-color: rgba(244, 67, 54, 0.5) !important; color: #ffcdd2; font-weight: bold; }
    .tz-booked-left { border-left: 2px solid #F44336 !important; }
    .tz-booked-right { border-right: 2px solid #F44336 !important; }
    
    /* Permanent Availability Column (Green) */
    .tz-avail { background-color: rgba(40, 167, 69, 0.3) !important; color: #4CAF50; font-weight: bold; }
    .tz-avail-left { border-left: 2px solid #28a745 !important; }
    .tz-avail-right { border-right: 2px solid #28a745 !important; }
    
    .sub-text { font-size: 11px; opacity: 0.7; display: block; margin-top: 4px; font-weight: normal;}

    /* --- RESPONSIVE HOVER EFFECTS (Bright Cyan) --- */
    .tz-table tbody tr:hover td:not(.tz-row-header) {
        background-color: rgba(0, 229, 255, 0.25) !important;
    }
    .tz-table td:not(.tz-row-header):hover::after, 
    .tz-table th:not(.tz-row-header):hover::after {
        content: ""; position: absolute; top: -5000px; left: 0; width: 100%; height: 10000px;
        background-color: rgba(0, 229, 255, 0.25); z-index: 1; pointer-events: none; 
    }
    .tz-table td:not(.tz-row-header):hover, 
    .tz-table th:not(.tz-row-header):hover {
        background-color: rgba(0, 229, 255, 0.9) !important; color: #121212 !important;
        box-shadow: inset 0 0 0 3px #00B8D4, 0 0 15px rgba(0, 229, 255, 0.8); cursor: crosshair; z-index: 5;
    }
    .tz-table td:not(.tz-row-header):hover *, .tz-table th:not(.tz-row-header):hover * {
        color: #121212 !important; font-weight: bold;
    }

    /* --- STICKY CLICK (FOCUS) EFFECTS (Ultra Bright Neon Yellow/Gold) --- */
    .tz-table tbody tr:focus-within td:not(.tz-row-header) {
        background-color: rgba(255, 234, 0, 0.3) !important; 
    }
    .tz-table td:not(.tz-row-header):focus::before {
        content: ""; position: absolute; top: -5000px; left: 0; width: 100%; height: 10000px;
        background-color: rgba(255, 234, 0, 0.3); z-index: 3; pointer-events: none; 
    }
    .tz-table td:not(.tz-row-header):focus {
        background-color: rgba(255, 234, 0, 0.95) !important; color: #121212 !important;
        box-shadow: inset 0 0 0 3px #FFD600, 0 0 20px rgba(255, 234, 0, 0.9); z-index: 6; outline: none; 
    }
    .tz-table td:not(.tz-row-header):focus * {
        color: #121212 !important; font-weight: bold;
    }

</style>
""", unsafe_allow_html=True)

# Reordered Time Zones
TZ_OPTIONS = {
    "Pacific Time (PT)": "America/Los_Angeles",
    "Kuala Lumpur (MYT)": "Asia/Kuala_Lumpur",
    "Mountain Time (MT)": "America/Denver",
    "Central Time (CT)": "America/Chicago",
    "Eastern Time (ET)": "America/New_York",
    "Alaska Time (AKT)": "America/Anchorage",
    "Hawaii Time (HT)": "Pacific/Honolulu",
    "London (UK)": "Europe/London",
    "Sydney (AEST)": "Australia/Sydney",
    "UTC / GMT": "UTC"
}

# Defined PST Schedule Blocks
AVAIL_HOURS = [9, 13, 15, 16] # 9 AM, 1 PM, 3 PM, 4 PM
BREAK_HOURS = [12]            # 12 PM
TRAINING_HOURS = [7]          # 7 AM

def get_cell_classes(h, booked_h_vals):
    classes = []
    if h in booked_h_vals:
        classes.append("tz-booked")
        if h - 1 not in booked_h_vals: classes.append("tz-booked-left")
        if h + 1 not in booked_h_vals: classes.append("tz-booked-right")
    elif h in BREAK_HOURS:
        classes.append("tz-break")
        if h - 1 not in BREAK_HOURS: classes.append("tz-break-left")
        if h + 1 not in BREAK_HOURS: classes.append("tz-break-right")
    elif h in TRAINING_HOURS:
        classes.append("tz-training")
        if h - 1 not in TRAINING_HOURS: classes.append("tz-training-left")
        if h + 1 not in TRAINING_HOURS: classes.append("tz-training-right")
    elif h in AVAIL_HOURS:
        classes.append("tz-avail")
        if h - 1 not in AVAIL_HOURS: classes.append("tz-avail-left")
        if h + 1 not in AVAIL_HOURS: classes.append("tz-avail-right")
    elif 7 <= h <= 16:
        classes.append("tz-working")
    return " ".join(classes)

st.title("🌍 Global Time Zone Dashboard")

# Perfectly leveled 3-left / 3-right legend
st.markdown("**Legend:**")
l_col1, l_col2 = st.columns(2)
with l_col1:
    st.markdown("🟣 **Purple**: Working Hours (7 AM - 5 PM PST)")
    st.markdown("🟢 **Green**: Available (9 AM - 10 AM, 1 PM - 2 PM, 3 PM - 5 PM PST)")
    st.markdown("🟡 **Yellow**: Break (12 PM PST)")
with l_col2:
    st.markdown("🔵 **Light Blue**: Training (7 AM PST)")
    st.markdown("🔴 **Red**: Booked Meetings")
    st.markdown("🖱️ **Interactive**: **Hover** for Blue Crosshair | **Click** a cell to lock!")

dashboard_placeholder = st.container()
st.divider()

# ==========================================
# PLANNER CONTROLS
# ==========================================
st.subheader("⚙️ Planner Controls")

with st.container(border=True):
    col1, col2, col3 = st.columns([1.5, 1, 1.5])
    with col1:
        selected_tzs = st.multiselect(
            "Select Time Zones to Display:", 
            options=list(TZ_OPTIONS.keys()), 
            default=["Pacific Time (PT)", "Kuala Lumpur (MYT)", "Mountain Time (MT)", "Central Time (CT)", "Eastern Time (ET)"]
        )
    with col2:
        time_format = st.radio("Time Format:", ["12-Hour (AM/PM)", "24-Hour"])
    with col3:
        meeting_options = {f"{h%12 or 12} {'AM' if h < 12 else 'PM'} PST": h for h in range(7, 18)}
        booked_hours = st.multiselect("🔴 Mark Booked Zoom Meetings (PST):", options=list(meeting_options.keys()), help="Select hours to highlight in red on the grid.")
        booked_h_vals = [meeting_options[k] for k in booked_hours]

# Set baseline timezone to PST
base_tz = pytz.timezone("America/Los_Angeles")
now_utc = datetime.utcnow().replace(tzinfo=pytz.utc)
current_live_time_pst = now_utc.astimezone(base_tz)

with dashboard_placeholder:
    if not selected_tzs:
        st.info("Please select at least one time zone from the controls below.")
    else:
        start_of_day = current_live_time_pst.replace(hour=0, minute=0, second=0, microsecond=0)
        html = '<div class="tz-container"><table class="tz-table">'
        html += '<tr><th class="tz-row-header">Time (Hour)</th>'
        for h in range(24):
            display_time = start_of_day + timedelta(hours=h)
            h_str = display_time.strftime("%I %p").lstrip("0").lower() if "12" in time_format else display_time.strftime("%H:00")
            cell_class = get_cell_classes(h, booked_h_vals)
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
                local_hour = tz_time.hour
                bg_class = "tz-day" if 7 <= local_hour < 19 else "tz-night"
                cell_class = f"{bg_class} {get_cell_classes(h, booked_h_vals)}"
                t_str = tz_time.strftime("%I %p").lstrip("0").lower() if "12" in time_format else tz_time.strftime("%H:00")
                date_str = tz_time.strftime("%b %d")
                html += f'<td class="{cell_class}" tabindex="0">{t_str}<br><span class="sub-text">{date_str}</span></td>'
            html += '</tr>'
        html += '</table></div>'
        st.markdown(html, unsafe_allow_html=True)

st.divider()

# ==========================================
# EMAIL TEMPLATE ASSISTANT
# ==========================================
st.header("✉️ Email Template Assistant")
st.markdown("Use this tool to automatically draft your follow-up email. It translates your fixed PST availability into the client's local time zone.")

with st.container(border=True):
    col_tz, col_ph, col_em, col_case = st.columns(4)
    with col_tz:
        target_tz_select = st.selectbox("Client Time Zone:", options=list(TZ_OPTIONS.keys()), index=2) # Default MT
    with col_ph:
        client_phone = st.text_input("Phone Number:", placeholder="e.g. 555-0198")
    with col_em:
        client_email = st.text_input("Email:", placeholder="e.g. client@domain.com")
    with col_case:
        case_number = st.text_input("Case Number:", placeholder="e.g. 00000000")

    support_phone = st.text_input("Your Support Line (number + option):", placeholder="e.g. 555-0100, option 2")

    # Dates Row (Auto-populating behavior)
    st.markdown("**Meeting Dates:**")
    d_col1, d_col2, d_col3 = st.columns(3)
    with d_col1:
        date1 = st.date_input("Day 1", value=datetime.today().date())
    with d_col2:
        date2 = st.date_input("Day 2", value=date1 + timedelta(days=1))
    with d_col3:
        date3 = st.date_input("Day 3", value=date1 + timedelta(days=2))

    # Booking / Slot Chopper
    st.markdown("**Chop Unavailable Slots (Mark as Booked):**")
    
    # Generate the slot options for the multiselect chopper
    slot_options = []
    for d_idx, d in enumerate([date1, date2, date3]):
        date_str = d.strftime('%m/%d/%Y')
        slot_options.extend([f"{date_str} - Slot 1", f"{date_str} - Slot 2", f"{date_str} - Slot 3"])
    
    booked_template_slots = st.multiselect(
        "Select specific slots to mark as 'Booked' in the table:", 
        options=slot_options,
        help="Use the dropdown to add multiple slots that are no longer available."
    )

st.subheader("📋 Output (Ready to Copy)")

# Convert PST fixed slots to Target Time Zone
target_tz_obj = pytz.timezone(TZ_OPTIONS[target_tz_select])
tz_abbr = target_tz_select.split("(")[-1].replace(")", "") # Extracts "MT" from "Mountain Time (MT)"

def get_slot_time_str(date_val, start_hour, end_hour):
    """Localizes PST base times to the selected date, then converts to the target TZ."""
    start_dt = base_tz.localize(datetime(date_val.year, date_val.month, date_val.day, start_hour, 0))
    end_dt = base_tz.localize(datetime(date_val.year, date_val.month, date_val.day, end_hour, 0))
    
    start_target = start_dt.astimezone(target_tz_obj)
    end_target = end_dt.astimezone(target_tz_obj)
    
    return f"{start_target.strftime('%I:%M %p').lstrip('0')} - {end_target.strftime('%I:%M %p').lstrip('0')}"

def get_cell_html(slot_key, d, start_h, end_h):
    """
    To fix the Outlook copy-paste bug, we explicitly set the color on the <td> element 
    rather than relying on a child <span>.
    """
    if slot_key in booked_template_slots:
        return f'<td style="border: 1px solid #e0e0e0; padding: 8px; text-align: center; color: #2e7d32;"><i><b>Booked</b></i></td>'
    else:
        time_str = get_slot_time_str(d, start_h, end_h)
        return f'<td style="border: 1px solid #e0e0e0; padding: 8px; text-align: center; color: #212121;">{time_str}</td>'

rows_html = ""
for d in [date1, date2, date3]:
    date_formatted = d.strftime('%m/%d/%Y')
    day_name = d.strftime('%A')
    
    s1_key = f"{date_formatted} - Slot 1"
    s1_td = get_cell_html(s1_key, d, 9, 10)
    
    s2_key = f"{date_formatted} - Slot 2"
    s2_td = get_cell_html(s2_key, d, 13, 14)
    
    s3_key = f"{date_formatted} - Slot 3"
    s3_td = get_cell_html(s3_key, d, 15, 17)
    
    rows_html += f"""<tr>
<td style="border: 1px solid #e0e0e0; padding: 8px; text-align: center; color: #212121;">{date_formatted}</td>
<td style="border: 1px solid #e0e0e0; padding: 8px; text-align: center; color: #212121;">{day_name}</td>
{s1_td}
{s2_td}
{s3_td}
<td style="border: 1px solid #e0e0e0; padding: 8px; text-align: center; color: #212121;">{tz_abbr}</td>
</tr>"""

# Note: The brackets `[]` have been entirely removed from the phone/email variables.
email_html = f"""<div style="font-family: sans-serif; font-size: 14px; color: #212121; line-height: 1.5; background-color: #ffffff; padding: 20px; border-radius: 8px; border: 2px solid #2196F3;">
<b>Following Up</b><br><br>
1. Would you prefer us to call or continue over email?<br>
2. If yes, is <b>{client_phone or 'PHONE NUMBER'}, {tz_abbr}</b> and <b>{client_email or 'EMAIL'}</b> the best way to reach you?<br>
3. We would like to do a screenshare, my current availability is shown below :<br><br>
<table style="border-collapse: collapse; width: 100%; max-width: 800px; border: 1px solid #e0e0e0;">
<tr style="background-color: #f8f9fa;">
<th style="border: 1px solid #e0e0e0; padding: 8px; text-align: center; color: #212121;">Date</th>
<th style="border: 1px solid #e0e0e0; padding: 8px; text-align: center; color: #212121;">Day</th>
<th style="border: 1px solid #e0e0e0; padding: 8px; text-align: center; color: #212121;">Slot 1</th>
<th style="border: 1px solid #e0e0e0; padding: 8px; text-align: center; color: #212121;">Slot 2</th>
<th style="border: 1px solid #e0e0e0; padding: 8px; text-align: center; color: #212121;">Slot 3</th>
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
You can reach us by replying to this email or calling {support_phone or 'SUPPORT PHONE'} (provide the case number <b>{case_number or 'CASE NUMBER'}</b>). We're available from 5.00 A.M. to 5.00 P.M. (Pacific Time), Monday through Friday.
</div>"""

st.markdown(email_html, unsafe_allow_html=True)