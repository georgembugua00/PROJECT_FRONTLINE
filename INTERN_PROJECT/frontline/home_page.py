import streamlit as st
import streamlit.components.v1 as components
from datetime import date, timedelta
from supabase import create_client, Client
from datetime import datetime
import pandas as pd
import time

SUPABASE_URL = "https://nzgdiyjdrfludykkzxiv.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im56Z2RpeWpkcmZsdWR5a2t6eGl2Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTIxMzYxNjQsImV4cCI6MjA2NzcxMjE2NH0.3lGOGA3FwOuLraw1Uv5-6BJ_iecrY5O9mN3RbXard7k"

# Initialize Supabase client
@st.cache_resource
def init_supabase():
    """Initialize Supabase client with credentials from Streamlit secrets."""
    url = SUPABASE_URL
    key = SUPABASE_KEY
    supabase: Client = create_client(url, key)
    return supabase

def get_employee_by_id(employee_id):
    """Fetches employee details by ID from Supabase."""
    supabase = init_supabase()
    try:
        response = supabase.table("employee_table").select("*").eq("uuid", employee_id).execute()
        if response.data:
            return response.data[0]
        return None
    except Exception as e:
        st.error(f"Error fetching employee by ID: {str(e)}")
        return None

def get_employee_by_name(employee_name):
    """Fetches employee details by name from Supabase."""
    supabase = init_supabase()
    try:
        response = supabase.table("employee_table").select("uuid, First_Name").eq("First_Name", employee_name).execute()
        if response.data:
            return response.data[0]
        return None
    except Exception as e:
        st.error(f"Error fetching employee by name: {str(e)}")
        return None

def apply_for_leave(employee_id, leave_type, start_date, end_date, description, attachment):
    """Adds a new leave application to the Supabase database."""
    supabase = init_supabase()
    try:
        response = supabase.table("off_roll_leave").insert({
            "employee_id": employee_id,
            "leave_type": leave_type,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "description": description,
            "attachment": bool(attachment),
            "status": "Pending"
        }).execute()
        if response.data:
            return True, "Leave request submitted successfully!"
        return False, "Failed to submit leave request"
    except Exception as e:
        return False, f"Error submitting leave request: {str(e)}"

def get_leave_history(employee_id):
    """Fetches the leave history for a specific employee from Supabase."""
    supabase = init_supabase()
    try:
        response = supabase.table("off_roll_leave").select(
            "leave_type, start_date, end_date, description, status, decline_reason, recall_leave"
        ).eq("employee_id", employee_id).order("start_date", desc=True).execute()

        if response.data:
            history = []
            for row in response.data:
                history.append((
                    row['leave_type'],
                    row['start_date'],
                    row['end_date'],
                    row['description'],
                    row['status'],
                    row.get('decline_reason'),
                    row.get('recall_reason')
                ))
            return history
        return []
    except Exception as e:
        st.error(f"Error fetching leave history: {str(e)}")
        return []

def get_all_pending_leaves():
    """Fetches all leave requests with a 'Pending' status for the manager from Supabase."""
    supabase = init_supabase()
    try:
        response = supabase.table("off_roll_leave").select(
            "AUUID, employee_id, leave_type, start_date, end_date, description, employee_table(First_Name)"
        ).eq("status", "Pending").execute()

        if response.data:
            pending_leaves = []
            for row in response.data:
                employee_name = row['employee_table']['First_Name'] if row['employee_table'] else None
                pending_leaves.append({
                    "id": row['uuid'],
                    "employee_name": employee_name,
                    "leave_type": row['leave_type'],
                    "start_date": row['start_date'],
                    "end_date": row['end_date'],
                    "description": row['description']
                })
            return pending_leaves
        return []
    except Exception as e:
        st.error(f"Error fetching pending leaves: {str(e)}")
        return []

def get_approved_leaves():
    """Fetches all leave requests with an 'Approved' status from Supabase."""
    supabase = init_supabase()
    try:
        response = supabase.table("off_roll_leave").select(
            "AUUID, employee_id, leave_type, start_date, end_date, description, employee_table(First_Name)"
        ).eq("status", "Approved").execute()

        if response.data:
            approved_leaves = []
            for row in response.data:
                employee_name = row['employee_table']['First_Name'] if row['employee_table'] else None
                approved_leaves.append({
                    "id": row['uuid'],
                    "employee_name": employee_name,
                    "leave_type": row['leave_type'],
                    "start_date": row['start_date'],
                    "end_date": row['end_date'],
                    "description": row['description']
                })
            return approved_leaves
        return []
    except Exception as e:
        st.error(f"Error fetching approved leaves: {str(e)}")
        return []

def update_leave_status(leave_id, new_status, reason=None):
    """Updates the status of a leave request in Supabase."""
    supabase = init_supabase()
    update_data = {"status": new_status}
    if new_status == "Declined":
        update_data["decline_reason"] = reason
    elif new_status == "Recalled":
        update_data["recall_reason"] = reason
    elif new_status == "Withdrawn":
        update_data["recall_reason"] = reason

    try:
        response = supabase.table("off_roll_leave").update(update_data).eq("employee_id", leave_id).execute()
        if response.data:
            return True, f"Leave status updated to {new_status}"
        return False, "Failed to update leave status"
    except Exception as e:
        return False, f"Error updating leave status: {str(e)}"

def get_team_leaves(status_filter=None, leave_type_filter=None, employee_filter=None):
    """Fetches all team leaves with optional filters for the manager's dashboard from Supabase."""
    supabase = init_supabase()
    try:
        query = supabase.table("off_roll_leave").select(
            "employee_id, leave_type, start_date, end_date, status, description, decline_reason, employee_table(First_Name)"
        )

        if status_filter:
            query = query.in_("status", status_filter)
        if leave_type_filter:
            query = query.in_("leave_type", leave_type_filter)
        if employee_filter and employee_filter != "All Team Members":
            query = query.eq("employee_table.First_Name", employee_filter)

        response = query.execute()

        if response.data:
            leaves = []
            for row in response.data:
                employee_name = row['employee_table']['First_Name'] if row['employee_table'] else None
                leaves.append({
                    "employee_name": employee_name,
                    "leave_type": row['leave_type'],
                    "start_date": row['start_date'],
                    "end_date": row['end_date'],
                    "status": row['status'],
                    "description": row['description'],
                    "decline_reason": row.get('decline_reason')
                })
            return leaves
        return []
    except Exception as e:
        st.error(f"Error fetching team leaves: {str(e)}")
        return []

def get_all_employees_from_db():
    """Gets a unique list of all employees from the employees table in Supabase."""
    supabase = init_supabase()
    try:
        response = supabase.table("employee_table").select("First_Name").order("First_Name", desc=False).execute()
        if response.data:
            employees = [row['First_Name'] for row in response.data]
            return employees
        return []
    except Exception as e:
        st.error(f"Error fetching employees: {str(e)}")
        return []

def get_all_leaves():
    """Fetches all leave records from Supabase, joining with employee names."""
    supabase = init_supabase()
    try:
        response = supabase.table("off_roll_leave").select(
            "AUUID, leave_type, start_date, end_date, description, status, employee_table(First_Name)"
        ).execute()

        if response.data:
            leaves = []
            for row in response.data:
                employee_name = row['employee_table']['First_Name'] if row['employee_table'] else None
                leaves.append({
                    "id": row["AUUID"],
                    "name": employee_name,
                    "type": row["leave_type"],
                    "start": row["start_date"],
                    "end": row["end_date"],
                    "description": row["description"],
                    "status": row["status"]
                })
            return leaves
        return []
    except Exception as e:
        st.error(f"Error fetching all leaves: {str(e)}")
        return []

def withdraw_leave(leave_id, recall_reason=None):
    """Marks a leave request as Withdrawn in Supabase with an optional reason."""
    return update_leave_status(leave_id, "Withdrawn", recall_reason)

def get_latest_leave_entry():
    """Fetches the details of the most recently added leave entry from Supabase."""
    supabase = init_supabase()
    try:
        response = supabase.table("off_roll_leave").select(
            "leave_type, start_date, end_date, description, status, decline_reason, recall_reason, employee_table(First_Name)"
        ).order("id", desc=True).limit(1).execute()

        if response.data:
            row = response.data[0]
            employee_name = row['employee_table']['First_Name'] if row['employee_table'] else None
            return {
                "employee_name": employee_name,
                "leave_type": row['leave_type'],
                "start_date": row['start_date'],
                "end_date": row['end_date'],
                "description": row['description'],
                "status": row['status'],
                "decline_reason": row.get('decline_reason'),
                "recall_reason": row.get('recall_reason')
            }
        return None
    except Exception as e:
        st.error(f"Error fetching latest leave entry: {str(e)}")
        return None

def get_employee_leave_entitlements(employee_id):
    """Fetches leave entitlements for a given employee from Supabase."""
    supabase = init_supabase()
    try:
        response = supabase.table("leave_entitlements").select("*").eq("employee_id", employee_id).execute()
        if response.data:
            return response.data[0]
        return None
    except Exception as e:
        st.error(f"Error fetching employee leave entitlements: {str(e)}")
        return None

def get_employee_used_leave(employee_id, leave_type=None):
    """Calculates total used leave days for an employee, optionally by type, from Supabase."""
    supabase = init_supabase()
    try:
        query = supabase.table("off_roll_leave").select("start_date, end_date").eq("employee_id", employee_id).eq("status", "Approved")
        if leave_type:
            query = query.eq("leave_type", leave_type)

        response = query.execute()
        used_days = 0
        if response.data:
            for record in response.data:
                start = datetime.fromisoformat(record['start_date'])
                end = datetime.fromisoformat(record['end_date'])
                used_days += (end - start).days + 1
        return int(used_days)
    except Exception as e:
        st.error(f"Error calculating used leave: {str(e)}")
        return 0

def get_current_user_profile(employee_id):
    """Fetches complete user profile including employee details and leave entitlements."""
    supabase = init_supabase()
    try:
        # Get employee details
        employee_response = supabase.table("employee_table").select("*").eq("uuid", employee_id).execute()
        
        if not employee_response.data:
            return None
            
        employee = employee_response.data[0]
        
        # Get leave entitlements
        entitlements_response = supabase.table("leave_entitlements").select("*").eq("employee_id", employee_id).execute()
        
        # Get used leave days
        used_leave = get_employee_used_leave(employee_id)
        
        # Build user profile
        user_profile = {
            "id": employee.get("uuid"),
            "name": employee.get("First_Name", ""),
            "surname": employee.get("Last_Name", ""),
            "email": employee.get("Email", ""),
            "position": employee.get("Position", "Agent"),
            "managing_partner": employee.get("Managing_Partner", "Airtel Kenya"),
            "franchise_type": employee.get("Franchise_Type", ""),
            "profile_pic": employee.get("Profile_Pic"),
            "used_leave": used_leave,
            "cumulative_leave": 0  # Default if no entitlements found
        }
        
        # Add entitlements if available
        if entitlements_response.data:
            entitlements = entitlements_response.data[0]
            user_profile["cumulative_leave"] = entitlements.get("annual_leave", 0)
            # You can add other leave types here if needed
            user_profile["sick_leave"] = entitlements.get("sick_leave", 0)
            user_profile["maternity_leave"] = entitlements.get("maternity_leave", 0)
            user_profile["paternity_leave"] = entitlements.get("paternity_leave", 0)
        
        return user_profile
        
    except Exception as e:
        st.error(f"Error fetching user profile: {str(e)}")
        return None

def profile_summary():
    """Display profile summary with data from database."""
    # Get employee ID from session state or use a default for demo
    # You should replace this with your actual authentication logic
    if 'employee_id' in st.session_state:
        employee_id = st.session_state.employee_id
    else:
        # For demo purposes, you might want to add a selector or use the first employee
        st.warning("No employee ID found in session. Please implement proper authentication.")
        return
    
    user = get_current_user_profile(employee_id)
    
    if not user:
        st.error("Unable to load user profile. Please try again.")
        return
    
    remaining_leave = user['cumulative_leave'] - user['used_leave']
    
    # Default profile pic if none provided
    default_pic = "https://media.istockphoto.com/id/1300845620/vector/user-icon-flat-isolated-on-white-background-user-symbol-vector-illustration.jpg?s=2048x2048&w=is&k=20&c=6hQNACQQjktni8CxSS_QSPqJv2tycskYmpFGzxv3FNs="
    profile_pic = user.get('profile_pic') or default_pic

    st.html(f"""
    <style>
        /* General Styling for Inter Font */
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap');
        body {{ font-family: 'Inter', sans-serif; }}

        /* Profile Card */
        .profile-card {{
            background: linear-gradient(135deg, #FF4B4B 0%, #CC0000 100%); /* Red gradient */
            padding: 30px; /* More padding */
            border-radius: 15px; /* More rounded corners */
            display: flex;
            align-items: center;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.4); /* Deeper, softer shadow */
            flex-wrap: wrap; 
            justify-content: center; 
            width: 100%; 
            box-sizing: border-box; 
            margin-bottom: 30px; /* Space below the card */
            border: 1px solid rgba(255, 255, 255, 0.1); /* Subtle white border */
            transition: transform 0.3s ease-in-out;
        }}
        .profile-card:hover {{
            transform: translateY(-5px); /* Slight lift on hover */
        }}

        /* Profile Image */
        .profile-img {{
            border-radius: 50%;
            width: 180px; /* Slightly smaller for aesthetics */
            height: 180px; 
            object-fit: cover;
            margin-right: 30px; /* More space */
            border: 4px solid #F0F0F0; /* Light border */
            box-shadow: 0 0 0 8px rgba(255, 255, 255, 0.2), 0 0 0 16px rgba(255, 255, 255, 0.1); /* Layered glow effect */
            flex-shrink: 0; 
            max-width: 100%; 
            transition: border-color 0.3s ease;
        }}
        .profile-img:hover {{
            border-color: #FFD700; /* Gold on hover */
        }}

        /* Profile Info */
        .profile-info {{
            flex-grow: 1;
            color: #FFFFFF; /* White text */
            min-width: 250px; /* Ensure readability */
            padding-top: 5px; 
            text-align: left;
            text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.3); /* Subtle text shadow */
        }}
        .profile-info h2 {{
            color: #FFFFFF;
            font-size: 2.2em; /* Larger name */
            margin-bottom: 5px;
            font-weight: 700; /* Bold */
            line-height: 1.2;
        }}
        .profile-info p {{
            font-size: 1em; /* Standard text size */
            margin-bottom: 3px;
            opacity: 0.9; /* Slightly faded */
            font-weight: 300; /* Lighter weight */
        }}

        /* Leave Stats Container */
        .leave-stats {{
            display: flex;
            gap: 20px; /* More space between cards */
            margin-top: 25px; /* More space from profile info */
            flex-wrap: wrap; 
            justify-content: center; 
            width: 100%; 
        }}

        /* Individual Leave Cards */
        .leave-card {{
            background-color: rgba(0, 0, 0, 0.3); /* Semi-transparent dark background */
            backdrop-filter: blur(5px); /* Frosted glass effect */
            padding: 15px 20px; /* More padding */
            border-radius: 12px; /* Rounded corners */
            text-align: center;
            border: 1px solid rgba(255, 255, 255, 0.2); /* Lighter border */
            color: #E0E0E0; /* Off-white text */
            flex: 1 1 150px; /* Flex item: grow, shrink, base-width */
            max-width: 180px; /* Max width for individual cards */
            box-sizing: border-box;
            min-width: 120px; 
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.3); /* Subtle card shadow */
            transition: transform 0.3s ease, background-color 0.3s ease;
        }}
        .leave-card:hover {{
            transform: translateY(-3px); /* Slight lift on hover */
            background-color: rgba(0, 0, 0, 0.4); /* Darker on hover */
        }}
        .leave-card > div:first-child {{
            font-size: 1.8em; /* Larger numbers */
            font-weight: 700; /* Bolder numbers */
            color: #FFFFFF; /* White numbers */
            margin-bottom: 5px;
        }}
        .leave-card > div:last-child {{
            font-size: 0.85em; /* Descriptive text size */
            opacity: 0.8;
        }}
        .leave-card.approved {{
            border-left: 5px solid #00E676; /* Brighter green for approved */
            background-color: rgba(0, 50, 0, 0.4); /* Slightly greenish tint */
        }}
        .leave-card.approved > div:first-child {{
            color: #98FB98; /* Light green for remaining days number */
        }}

        /* Media Queries for smaller screens */
        @media (max-width: 768px) {{
            .profile-card {{
                flex-direction: column; 
                align-items: center; 
                padding: 20px; 
                margin-bottom: 20px;
            }}
            .profile-img {{
                width: 120px; 
                height: 120px; 
                margin-right: 0; 
                margin-bottom: 20px; 
                border: 3px solid #F0F0F0;
                box-shadow: 0 0 0 6px rgba(255, 255, 255, 0.2);
            }}
            .profile-info {{
                text-align: center; 
                width: 100%; 
                min-width: unset; 
            }}
            .profile-info h2 {{
                font-size: 1.8em; 
            }}
            .profile-info p {{
                font-size: 0.9em; 
            }}
            .leave-stats {{
                flex-direction: row; 
                flex-wrap: wrap; 
                justify-content: center; 
                gap: 10px; 
                margin-top: 15px;
            }}
            .leave-card {{
                flex: 1 1 45%; /* Allow 2 cards per row on small screens */
                max-width: 48%; /* Max width to fit two per row */
                padding: 12px 10px; 
                font-size: 0.9em; 
            }}
            .leave-card > div:first-child {{
                font-size: 1.4em; 
            }}
            .leave-card > div:last-child {{
                font-size: 0.8em; 
            }}
        }}

        @media (max-width: 480px) {{
            .leave-stats {{
                flex-direction: column; /* Stack cards fully on very small screens */
                align-items: center; /* Center them */
            }}
            .leave-card {{
                width: 90%; /* Take nearly full width */
                max-width: 250px; /* Cap max width for very narrow screens */
            }}
        }}
    </style>

    <div class="profile-card">
        <img src="{profile_pic}" class="profile-img">
        <div class="profile-info">
            <h2>{user['name']} {user['surname']}</h2>
            <p>📌 {user['position']}</p>
            <p>🏢 {user['managing_partner']}</p>
            <p>🏷️ {user['franchise_type']}</p>
            
            <div class="leave-stats">
                <div class="leave-card">
                    <div>{user['cumulative_leave']}</div>
                    <div>Cumulative Days</div>
                </div>
                <div class="leave-card">
                    <div>{user['used_leave']}</div>
                    <div>Used Days</div>
                </div>
                <div class="leave-card approved">
                    <div>{remaining_leave}</div>
                    <div>Remaining Days</div>
                </div>
            </div>
        </div>
    </div>
    """)

# --- Home Page ---
slideshow_html = """
<div class="slideshow-container">
  <div class="mySlides fade">
    <img src="https://cdn-webportal.airtelstream.net/website/kenya/assets/images/opco/offers/Send-Money-for%20Free-Web%20Banners.jpg" alt="Airtel Offer 1">
  </div>
  <div class="mySlides fade">
    <img src="https://cdn-webportal.airtelstream.net/website/kenya/assets/images/opco/offers/2GB-@-99-Bob-web-banners.jpg" alt="Airtel Offer 2">
  </div>
  <div class="mySlides fade">
    <img src="https://cdn-webportal.airtelstream.net/website/kenya/assets/images/opco/offers/1GB-@15-Bob-web-banners.jpg" alt="Airtel Offer 3">
  </div>
  <div class="mySlides fade">
    <img src="https://cdn-webportal.airtelstream.net/website/kenya/assets/images/AIRTEL-KENYA_HVC_CAMPAIGN_700_by_700_1.jpg" alt="Airtel Offer 4">
</div>
<div style="text-align:center; padding: 15px 0;">
  <span class="dot"></span> 
  <span class="dot"></span> 
  <span class="dot"></span> 
  <span class="dot"></span>
</div>

<script>
let slideIndex = 0;
function showSlides() {
  let i;
  let slides = document.getElementsByClassName("mySlides");
  let dots = document.getElementsByClassName("dot");
  for (i = 0; i < slides.length; i++) {
    slides[i].style.display = "none";  
  }
  slideIndex++;
  if (slideIndex > slides.length) {slideIndex = 1}    
  for (i = 0; i < dots.length; i++) {
    dots[i].className = dots[i].className.replace(" active", "");
  }
  slides[slideIndex-1].style.display = "block";  
  dots[slideIndex-1].className += " active";
  setTimeout(showSlides, 5000);
}

document.addEventListener('DOMContentLoaded', showSlides);
</script>

<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap');
body { font-family: 'Inter', sans-serif; }

.slideshow-container { 
    width: 100%; 
    max-width: 900px;
    position: relative; 
    margin: 20px auto;
    overflow: hidden;
    border-radius: 12px;
    box-shadow: 0 8px 25px rgba(0, 0, 0, 0.4);
    background-color: #1a1a1a;
}

.mySlides { 
    display: none; 
    width: 100%;
    height: auto;
    text-align: center;
}

.mySlides img {
    width: 100%;
    height: auto;
    display: block;
    border-radius: 12px;
    object-fit: cover;
}

.dot { 
    height: 12px;
    width: 12px; 
    margin: 0 4px;
    background-color: #666;
    border-radius: 50%; 
    display: inline-block; 
    transition: background-color 0.4s ease, transform 0.2s ease;
    cursor: pointer;
}

.dot.active { 
    background-color: #FF4B4B;
    transform: scale(1.2);
}

.dot:hover {
    background-color: #FF6F6F;
}

.fade {
  -webkit-animation-name: fade;
  -webkit-animation-duration: 1.5s;
  animation-name: fade;
  animation-duration: 1.5s;
}

@-webkit-keyframes fade {
  from {opacity: .7} 
  to {opacity: 1}
}

@keyframes fade {
  from {opacity: .7} 
  to {opacity: 1}
}

@media (max-width: 768px) {
    .slideshow-container {
        margin: 15px auto;
        border-radius: 8px;
    }
    .dot {
        height: 10px;
        width: 10px;
        margin: 0 3px;
    }
}
</style>
"""

# Global styling
st.html("""
    <style>
    .stApp {
        background-color: #0d0d0d;
        color: #F0F0F0;
        font-family: 'Inter', sans-serif;
    }
    .css-1d3f8gq {
        padding-top: 1rem;
        padding-right: 1rem;
        padding-left: 1rem;
        padding-bottom: 1rem;
    }
    h1, h2, h3, h4, h5, h6 {
        color: #FF4B4B;
        font-weight: 700;
        text-shadow: 1px 1px 2px rgba(0,0,0,0.2);
    }
    hr {
        border-top: 1px solid rgba(255, 255, 255, 0.1);
    }
    </style>
""")

# Main app logic
#st.header("Channel Partner Management System")
st.markdown("---")

if 'employee_id' not in st.session_state:
    employees = get_all_employees_from_db()
    
    # Fallback to default employee "George"
    default_employee = next((emp for emp in employees if emp == "George"), None)
    
    st.sidebar.write("Demo Mode: Select an employee (default is George)")
    selected_employee = st.sidebar.selectbox(
        "Select Employee", 
        employees, 
        index=employees.index(default_employee) if default_employee else 0
    )

    if selected_employee:
        employee_data = get_employee_by_name(selected_employee)
        if employee_data:
            st.session_state.employee_id = employee_data['uuid']


profile_summary()
st.subheader("📢 Latest Offers")
components.html(slideshow_html, height=500)

approved_leaves = get_team_leaves(status_filter=["Approved"])
events = []
for leave in approved_leaves:
    events.append({
        "title": f'{leave["employee_name"]} - {leave["leave_type"]}',
        "start": leave["start_date"],
        "end": leave["end_date"],
    })

try:
    from streamlit_calendar import calendar
    calendar(events=events)
except ImportError:
    st.write(events)