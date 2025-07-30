import streamlit as st
from datetime import date, timedelta
#DATABASE LOGIC
import sqlite3
from datetime import date
import streamlit as st
from datetime import datetime
import pandas as pd

# --- SQLite Database Configuration ---
# Ensure this path is correct and accessible by your Streamlit app
DB_NAME = "leave_management.db"

def init_db():
    """Initializes and returns a connection to the SQLite database."""
    try:
        conn = sqlite3.connect(DB_NAME)
        conn.row_factory = sqlite3.Row  # This allows accessing columns by name (e.g., row['column_name'])
        return conn
    except sqlite3.Error as e:
        st.error(f"Error connecting to database: {e}")
        return None

def create_tables():
    """
    Creates necessary tables if they don't exist based on the provided schemas.
    IMPORTANT: Ensures 'status' column is present in 'off_roll'/'leave' table
    and handles 'decline_reason'/'recall_reason' defaults.
    """
    conn = init_db()
    if conn:
        try:
            cursor = conn.cursor()

            # 1. Create employee_table_rows
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS "employee_table" (
                    "Username"	INTEGER,
                    "First_Name"	TEXT,
                    "Middle_Name"	TEXT,
                    "Surname_Name"	TEXT,
                    "AUUID"	INTEGER,
                    "Employee_ID"	INTEGER,
                    "Email"	TEXT,
                    "Manager"	TEXT,
                    "Date_of_Join"	TEXT,
                    "OPCO_Region"	TEXT,
                    "Organization"	TEXT,
                    "Department"	TEXT,
                    "Sub_Department"	TEXT,
                    "Person_Type"	TEXT,
                    "Personal_Mobile"	INTEGER,
                    "Partner_Name"	TEXT,
                    "id"	INTEGER PRIMARY KEY AUTOINCREMENT,
                    "uuid"	TEXT UNIQUE, -- Assuming 'uuid' is the unique identifier for external linking
                    "gender"	TEXT,
                    "password"	TEXT,
                    "position"	TEXT
                );
            """)

            # 2. Create off_roll (This was 'leave' in your previous snippet but 'off_roll' in the employee file)
            # Consistency is key. Assuming 'off_roll' as the master table for leave applications.
            # If 'leave' is a separate table, define its schema clearly.
            # For now, I will use 'off_roll' as used in employee_leave.py, assuming this manager view
            # is managing 'off_roll' entries. If you truly have a table named 'leave' for this view,
            # please provide its exact schema.
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS "leave_entries" (
                    "leave_id"	INTEGER PRIMARY KEY AUTOINCREMENT,
                    "employee_id"   TEXT NOT NULL, -- Links to employee_table_rows.uuid
                    "employee_name"	TEXT NOT NULL,
                    "leave_type"	TEXT NOT NULL,
                    "start_date"	TEXT NOT NULL,
                    "end_date"	TEXT NOT NULL,
                    "description"	TEXT DEFAULT '', -- Made nullable, set default to empty string if NOT NULL
                    "attachment"	INTEGER DEFAULT 0, -- BOOLEAN is INTEGER in SQLite (0 or 1)
                    "status"    TEXT DEFAULT 'Pending', -- CRITICAL ADDITION
                    "decline_reason"    TEXT DEFAULT '', -- Default empty string due to NOT NULL
                    "recall_reason" TEXT DEFAULT '', -- Default empty string due to NOT NULL
                    FOREIGN KEY ("employee_id") REFERENCES "employee_table_rows"("uuid")
                );
            """)

            # 3. Create leave_entitlements (Corrected name from "leave_entitlements (1)")
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS "leave_entitlements" (
                    "employee_id"	TEXT PRIMARY KEY, -- Links to employee_table_rows.uuid
                    "annual_leave"	INTEGER NOT NULL,
                    "sick_leave"	INTEGER NOT NULL,
                    "compensation_leave"	INTEGER NOT NULL,
                    "maternity_leave_days"	INTEGER NOT NULL,
                    "paternity_leave_days"	INTEGER NOT NULL,
                    FOREIGN KEY("employee_id") REFERENCES "employee_table_rows"("uuid")
                );
            """)
            conn.commit()
        except sqlite3.Error as e:
            st.error(f"Error creating tables: {e}")
        finally:
            conn.close()

# Call create_tables once when the application starts
create_tables()

# --- Employee Data Retrieval Functions ---

def get_employee_by_id(employee_uuid):
    """Fetches employee details by UUID from employee_table"""
    conn = init_db()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT uuid, First_Name, Surname_Name, Email FROM employee_table WHERE uuid = ?", (employee_uuid,))
            employee = cursor.fetchone()
            if employee:
                return dict(employee)
            return None
        except sqlite3.Error as e:
            st.error(f"Error fetching employee by ID: {str(e)}")
            return None
        finally:
            conn.close()
    return None

def get_employee_by_name(employee_name):
    """Fetches employee details by First_Name from employee_table"""
    conn = init_db()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT uuid, First_Name FROM employee_table WHERE First_Name = ?", (employee_name,))
            employee = cursor.fetchone()
            if employee:
                return dict(employee)
            return None
        except sqlite3.Error as e:
            st.error(f"Error fetching employee by name: {str(e)}")
            return None
        finally:
            conn.close()
    return None

def get_all_employees_from_db():
    """Fetches all employee names from employee_table_rows."""
    conn = init_db()
    employees = []
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT First_Name, Surname_Name, uuid FROM employee_table ORDER BY First_Name")
            rows = cursor.fetchall()
            employees = [f"{row['First_Name']} {row['Surname_Name']}" for row in rows if row['First_Name'] and row['Surname_Name']]
        except sqlite3.Error as e:
            st.error(f"Error fetching all employees: {str(e)}")
        finally:
            conn.close()
    return employees

# --- Leave Application Management Functions (for Manager) ---

def get_all_pending_leaves():
    """Fetches all pending leave requests from the 'off_roll' table."""
    conn = init_db()
    pending_leaves = []
    if conn:
        try:
            cursor = conn.cursor()
            # Changed 'leave' to 'off_roll' for consistency with employee_leave.py
            cursor.execute("""
                SELECT leave_id, employee_name, leave_type, start_date, end_date, description, status
                FROM leave_entries
                WHERE status = 'Pending'
                ORDER BY start_date ASC
            """)
            pending_leaves = cursor.fetchall()
            return [dict(row) for row in pending_leaves]
        except sqlite3.Error as e:
            st.error(f"Error fetching all pending leaves: {str(e)}")
            return []
        finally:
            conn.close()
    return []

def get_approved_leaves():
    """Fetches all approved leave requests from the 'off_roll' table."""
    conn = init_db()
    approved_leaves = []
    if conn:
        try:
            cursor = conn.cursor()
            # Changed 'leave' to 'off_roll'
            cursor.execute("""
                SELECT leave_id, employee_name, leave_type, start_date, end_date, description, status
                FROM leave_entries
                WHERE status = 'Approved'
                ORDER BY start_date ASC
            """)
            approved_leaves = cursor.fetchall()
            return [dict(row) for row in approved_leaves]
        except sqlite3.Error as e:
            st.error(f"Error fetching approved leaves: {str(e)}")
            return []
        finally:
            conn.close()
    return []

def get_team_leaves(status_filter=None, leave_type_filter=None, employee_filter=None):
    """
    Fetches leave requests based on filters for the team dashboard.
    status_filter: list of strings (e.g., ['Pending', 'Approved'])
    leave_type_filter: list of strings (e.g., ['Annual', 'Sick'])
    employee_filter: string (e.g., 'John Doe')
    """
    conn = init_db()
    filtered_leaves = []
    if conn:
        try:
            cursor = conn.cursor()
            query_sql = "SELECT leave_id, employee_name, leave_type, start_date, end_date, description, status, decline_reason, recall_reason FROM leave_entries WHERE 1=1"
            params = []

            if status_filter:
                placeholders = ','.join('?' for _ in status_filter)
                query_sql += f" AND status IN ({placeholders})"
                params.extend(status_filter)
            
            if leave_type_filter:
                placeholders = ','.join('?' for _ in leave_type_filter)
                query_sql += f" AND leave_type IN ({placeholders})"
                params.extend(leave_type_filter)

            if employee_filter and employee_filter != "All Team Members":
                query_sql += " AND employee_name = ?"
                params.append(employee_filter)

            query_sql += " ORDER BY start_date DESC"
            
            cursor.execute(query_sql, tuple(params))
            filtered_leaves = cursor.fetchall()
            return [dict(row) for row in filtered_leaves]
        except sqlite3.Error as e:
            st.error(f"Error fetching team leaves: {str(e)}")
            return []
        finally:
            conn.close()
    return []

def update_leave_status(leave_request_id, new_status, reason=""):
    """Updates the status of a leave request in 'off_roll' table."""
    if not leave_request_id:
        return False, "Invalid leave ID"
        
    conn = init_db()
    if conn:
        try:
            cursor = conn.cursor()
            update_sql = "UPDATE leave_entries SET status = ?"
            params = [new_status]

            if new_status == "Declined":
                update_sql += ", decline_reason = ?, recall_reason = ''" # Clear recall reason
                params.append(reason)
            elif new_status == "Recalled":
                update_sql += ", recall_reason = ?, decline_reason = ''" # Clear decline reason
                params.append(reason)
            elif new_status == "Approved": # Clear both reasons if approved
                update_sql += ", decline_reason = '', recall_reason = ''"
            
            update_sql += " WHERE id = ?" # Use 'id' as the primary key of 'off_roll'
            params.append(leave_request_id)

            cursor.execute(update_sql, tuple(params))
            conn.commit()

            if cursor.rowcount > 0:
                return True, f"Leave status updated to {new_status}"
            else:
                return False, "Failed to update leave status (leave request not found)."
        except sqlite3.Error as e:
            return False, f"Error updating leave status: {str(e)}"
        finally:
            conn.close()
    return False, "Database connection failed."

# --- Leave Policies & UI elements (No changes needed if these are just display) ---
LEAVE_TYPE_MAPPING = {
    "Annual": "annual_leave",
    "Sick": "sick_leave",
    "Maternity": "maternity_leave_days",
    "Paternity": "paternity_leave_days",
    "Study": "compensation_leave",
    "Compensation": "compensation_leave",
    "Compassionate": "compensation_leave",
    "Unpaid": None
}

st.set_page_config(layout="wide")



# --- UI Header ---
st.html("""
<style>
    .header-style {
        background-color: #f0f2f6;
        padding: 20px;
        border-radius: 10px;
        text-align: center;
        margin-bottom: 30px;
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
    }
    .header-style h1 {
        color: #2c3e50;
        font-size: 2.5em;
        margin-bottom: 5px;
    }
    .header-style p {
        color: #7f8c8d;
        font-size: 1.1em;
    }
    .stButton>button {
        background-color: #4CAF50;
        color: white;
        border-radius: 5px;
        padding: 10px 20px;
        font-size: 16px;
        border: none;
        cursor: pointer;
        transition: background-color 0.3s ease;
    }
    .stButton>button:hover {
        background-color: #45a049;
    }
    .stButton>button[key*="decline"] {
        background-color: #e74c3c;
    }
    .stButton>button[key*="decline"]:hover {
        background-color: #c0392b;
    }
    .stButton>button[key*="recall"] {
        background-color: #f39c12;
    }
    .stButton>button[key*="recall"]:hover {
        background-color: #e67e22;
    }
    .stExpander {
        border: 1px solid #e0e0e0;
        border-radius: 8px;
        padding: 15px;
        margin-bottom: 15px;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
    }
</style>
<div class="header-style">
    <h1>📅 Leave Request Manager</h1>
    <p style="margin: 0; opacity: 0.9;">Review and manage employee leave requests</p>
</div>
""")

# --- Manager Views ---

def pending_leaves_view():
    st.header("Pending Leave Requests for Review")
    pending_leaves = get_all_pending_leaves()

    if not pending_leaves:
        st.success("✨ All caught up! There are no pending leave requests.")
        return

    for leave in pending_leaves:
        employee_id_for_ui = leave["id"] # This is the 'id' from the off_roll table
        employee_name = leave["employee_name"]
        leave_type = leave["leave_type"]
        start_date = leave["start_date"]
        end_date = leave["end_date"]
        description = leave["description"]

        with st.expander(f"Request from {employee_name} ({leave_type}) - {start_date} to {end_date}", expanded=True):
            st.write(f"**Employee:** {employee_name}")
            st.write(f"**Leave Type:** {leave_type}")
            st.write(f"**Dates:** {start_date} to {end_date}")
            st.write(f"**Reason:** {description if description else 'No description provided.'}")

            col1, col2 = st.columns([1, 1])
            with col1:
                if st.button("✅ Approve", key=f"approve_{employee_id_for_ui}"):
                    update_leave_status(employee_id_for_ui, "Approved")
                    st.success(f"Leave for {employee_name} approved.")
                    st.rerun()
            with col2:
                # Toggle visibility of the decline reason input
                if f"show_reason_{employee_id_for_ui}" not in st.session_state:
                    st.session_state[f"show_reason_{employee_id_for_ui}"] = False
                
                if st.button("❌ Decline", key=f"decline_{employee_id_for_ui}"):
                    st.session_state[f"show_reason_{employee_id_for_ui}"] = not st.session_state[f"show_reason_{employee_id_for_ui}"]
                    # If button is clicked to hide, don't show the input immediately
                    if not st.session_state[f"show_reason_{employee_id_for_ui}"]:
                        st.rerun() # Rerun to remove the text input
                
                if st.session_state[f"show_reason_{employee_id_for_ui}"]:
                    decline_reason = st.text_input("Reason for declining:", key=f"reason_{employee_id_for_ui}")
                    if st.button("Confirm Decline", key=f"confirm_decline_{employee_id_for_ui}"):
                        if decline_reason:
                            update_leave_status(employee_id_for_ui, "Declined", reason=decline_reason)
                            st.error(f"Leave for {employee_name} declined.")
                            st.rerun()
                        else:
                            st.warning("A reason is required to decline a request.")


def approved_leaves_for_recall_view():
    st.header("Approved Leaves (for Recall)")
    approved_leaves = get_approved_leaves()

    if not approved_leaves:
        st.info("No approved leaves currently.")
        return

    for leave in approved_leaves:
        leave_id = leave["id"] # This is the 'id' from the off_roll table
        employee_name = leave["employee_name"]
        leave_type = leave["leave_type"]
        start_date_str = leave["start_date"]
        end_date_str = leave["end_date"]
        description = leave["description"]

        # Safe date parsing
        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
        except ValueError:
            st.error(f"⚠️ Invalid date format in leave ID {leave_id} for {employee_name}: {start_date_str} to {end_date_str}")
            continue

        today = date.today()

        # Calculate remaining days
        if today > end_date:
            days_left = 0
        elif today < start_date:
            days_left = (end_date - start_date).days + 1
        else:
            days_left = (end_date - today).days + 1

        with st.expander(f"Approved Leave for {employee_name} ({leave_type}) - {start_date_str} to {end_date_str}", expanded=True):
            st.write(f"**Employee:** {employee_name}")
            st.write(f"**Leave Type:** {leave_type}")
            st.write(f"**Dates:** {start_date_str} to {end_date_str}")
            st.write(f"**Reason:** {description if description else 'No description provided.'}")
            st.write(f"**Days Remaining:** {days_left}")

            if st.button("↩️ Recall Leave", key=f"recall_{leave_id}"):
                # The original logic checks if days_left > 3 before allowing recall.
                # You might want to adjust this policy.
                if days_left > 3:
                    recall_reason = "Operational Need" # You might want a text input for this too
                    update_leave_status(leave_id, "Recalled", reason=recall_reason)
                    st.warning(f"Leave for {employee_name} has been recalled due to {recall_reason}.")
                    st.rerun()
                else:
                    st.error(f"Cannot recall leave for {employee_name}. Less than 3 days ({days_left} days) remaining or leave has ended.")

def team_leaves_dashboard_view():
    st.header("Team Leave Dashboard")

    all_employees = ["All Team Members"] + get_all_employees_from_db()
    
    col1, col2, col3 = st.columns(3)
    with col1:
        selected_employee = st.selectbox("Filter by Employee", all_employees)
    with col2:
        selected_status = st.multiselect("Filter by Status", ["Pending", "Approved", "Declined", "Withdrawn", "Recalled"], default=["Pending", "Approved"])
    with col3:
        all_leave_types = list(LEAVE_TYPE_MAPPING.keys()) # Get keys from mapping for consistency
        selected_leave_type = st.multiselect("Filter by Leave Type", all_leave_types)

    filtered_leaves = get_team_leaves(
        status_filter=selected_status if selected_status else None,
        leave_type_filter=selected_leave_type if selected_leave_type else None,
        employee_filter=selected_employee if selected_employee != "All Team Members" else None
    )

    if not filtered_leaves:
        st.info("No team leaves found matching the selected filters.")
        return

    st.subheader("Filtered Team Leaves")
    leave_data = []
    for leave in filtered_leaves:
        leave_data.append({
            "Employee": leave["employee_name"],
            "Leave Type": leave["leave_type"],
            "Start Date": leave["start_date"],
            "End Date": leave["end_date"],
            "Status": leave["status"],
            "Description": leave["description"] if leave["description"] else "N/A",
            "Decline Reason": leave["decline_reason"] if leave["decline_reason"] else "N/A",
            "Recall Reason": leave["recall_reason"] if leave["recall_reason"] else "N/A" # Added recall reason
        })

    # Display results in a table for better readability
    # Convert to DataFrame for better display features in Streamlit
    df = pd.DataFrame(leave_data)
    st.dataframe(df, use_container_width=True)




# Ultra-modern CSS with glassmorphism and advanced animations
def inject_premium_css():
    st.html("""
                <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');
        
        .stApp {
            background: linear-gradient(135deg, #1f1f1f 0%, #000000 50%, #1a1a1a 100%);
            font-family: 'Inter', sans-serif;
            color: white;
        }
        
        .main .block-container {
            padding-top: 2rem;
            padding-bottom: 2rem;
            max-width: 1400px;
        }
        
        /* Premium glassmorphism cards with red accents */
        .glass-card {
            background: rgba(255, 255, 255, 0.05);
            backdrop-filter: blur(20px);
            border-radius: 20px;
            border: 1px solid rgba(220, 38, 38, 0.3);
            padding: 2rem;
            margin: 1rem 0;
            box-shadow: 0 20px 40px rgba(0, 0, 0, 0.3);
            transition: all 0.3s ease;
            position: relative;
            overflow: hidden;
        }
        
        .glass-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 30px 60px rgba(220, 38, 38, 0.2);
            border-color: rgba(220, 38, 38, 0.5);
        }
        
        .glass-card::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 3px;
            background: linear-gradient(90deg, #dc2626, #ef4444, #f87171, #dc2626);
            background-size: 200% 100%;
            animation: redShimmer 3s ease-in-out infinite;
        }
        
        @keyframes redShimmer {
            0%, 100% { background-position: 200% 0; }
            50% { background-position: -200% 0; }
        }
        
        /* Premium sidebar with black theme */
        .css-1d391kg {
            background: rgba(0, 0, 0, 0.8);
            backdrop-filter: blur(20px);
            border-right: 2px solid rgba(220, 38, 38, 0.3);
        }
        
        /* Notification bell with red pulse animation */
        .notification-container {
            position: relative;
            display: inline-block;
        }
        
        .notification-bell {
            font-size: 2rem;
            color: #dc2626;
            animation: redPulse 2s infinite;
            cursor: pointer;
            transition: all 0.3s ease;
        }
        
        .notification-bell:hover {
            transform: scale(1.2);
            color: #ef4444;
            filter: drop-shadow(0 0 10px #dc2626);
        }
        
        @keyframes redPulse {
            0% { transform: scale(1); color: #dc2626; }
            50% { transform: scale(1.1); color: #ef4444; }
            100% { transform: scale(1); color: #dc2626; }
        }
        
        .notification-badge {
            position: absolute;
            top: -5px;
            right: -5px;
            background: linear-gradient(45deg, #dc2626, #ef4444);
            color: white;
            border-radius: 50%;
            width: 24px;
            height: 24px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 0.8rem;
            font-weight: 700;
            animation: redBounce 1s infinite;
            box-shadow: 0 0 10px rgba(220, 38, 38, 0.5);
        }
        
        @keyframes redBounce {
            0%, 20%, 50%, 80%, 100% { transform: translateY(0); }
            40% { transform: translateY(-5px); }
            60% { transform: translateY(-3px); }
        }
        
        /* Status badges with red theme */
        .status-badge {
            display: inline-block;
            padding: 0.6rem 1.2rem;
            border-radius: 25px;
            font-weight: 700;
            font-size: 0.85rem;
            text-transform: uppercase;
            letter-spacing: 0.8px;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.3);
            transition: all 0.3s ease;
        }
        
        .status-pending {
            background: linear-gradient(45deg, #dc2626, #ef4444);
            color: white;
            box-shadow: 0 4px 20px rgba(220, 38, 38, 0.4);
        }
        
        .status-approved {
            background: linear-gradient(45deg, #1f1f1f, #374151);
            color: white;
            border: 1px solid #dc2626;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.4);
        }
        
        .status-declined {
            background: linear-gradient(45deg, #991b1b, #7f1d1d);
            color: white;
            box-shadow: 0 4px 20px rgba(153, 27, 27, 0.4);
        }
        
        .status-recalled {
            background: linear-gradient(45deg, #b91c1c, #991b1b);
            color: white;
            box-shadow: 0 4px 20px rgba(185, 28, 28, 0.4);
        }
        
        /* Premium buttons with red theme */
        .premium-btn {
            background: linear-gradient(45deg, #dc2626, #991b1b);
            border: none;
            border-radius: 25px;
            color: white;
            padding: 0.75rem 2rem;
            font-weight: 700;
            cursor: pointer;
            transition: all 0.3s ease;
            box-shadow: 0 8px 25px rgba(220, 38, 38, 0.3);
            position: relative;
            overflow: hidden;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        
        .premium-btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 12px 35px rgba(220, 38, 38, 0.5);
            background: linear-gradient(45deg, #ef4444, #dc2626);
        }
        
        .premium-btn::before {
            content: '';
            position: absolute;
            top: 0;
            left: -100%;
            width: 100%;
            height: 100%;
            background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.2), transparent);
            transition: left 0.5s;
        }
        
        .premium-btn:hover::before {
            left: 100%;
        }
        
        .danger-btn {
            background: linear-gradient(45deg, #7f1d1d, #450a0a);
            box-shadow: 0 8px 25px rgba(127, 29, 29, 0.3);
        }
        
        .danger-btn:hover {
            box-shadow: 0 12px 35px rgba(127, 29, 29, 0.5);
        }
        
        /* Employee cards with black/red theme */
        .employee-card {
            background: rgba(0, 0, 0, 0.4);
            border-radius: 15px;
            padding: 1.5rem;
            margin: 1rem 0;
            border: 1px solid rgba(220, 38, 38, 0.2);
            transition: all 0.3s ease;
            position: relative;
        }
        
        .employee-card:hover {
            background: rgba(0, 0, 0, 0.6);
            transform: translateX(10px);
            border-color: rgba(220, 38, 38, 0.5);
            box-shadow: 0 10px 30px rgba(220, 38, 38, 0.2);
        }
        
        .employee-avatar {
            width: 60px;
            height: 60px;
            border-radius: 50%;
            background: linear-gradient(45deg, #dc2626, #991b1b);
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.5rem;
            color: white;
            font-weight: 700;
            margin-bottom: 1rem;
            border: 2px solid rgba(255, 255, 255, 0.1);
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.3);
        }
        
        /* Leave type icons */
        .leave-type-icon {
            font-size: 2rem;
            margin-right: 0.5rem;
            vertical-align: middle;
            filter: drop-shadow(0 2px 4px rgba(0, 0, 0, 0.3));
        }
        
        /* Stats cards with red/black gradients */
        .stats-card {
            background: linear-gradient(135deg, rgba(0, 0, 0, 0.6), rgba(31, 31, 31, 0.4));
            border-radius: 20px;
            padding: 2rem;
            text-align: center;
            border: 1px solid rgba(220, 38, 38, 0.3);
            transition: all 0.3s ease;
            position: relative;
            overflow: hidden;
        }
        
        .stats-card:hover {
            transform: scale(1.05);
            border-color: rgba(220, 38, 38, 0.6);
            box-shadow: 0 15px 40px rgba(220, 38, 38, 0.2);
        }
        
        .stats-card::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: linear-gradient(45deg, transparent, rgba(220, 38, 38, 0.1), transparent);
            opacity: 0;
            transition: opacity 0.3s ease;
        }
        
        .stats-card:hover::before {
            opacity: 1;
        }
        
        .stats-number {
            font-size: 3rem;
            font-weight: 900;
            background: linear-gradient(45deg, #dc2626, #ef4444, #f87171);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            text-shadow: 0 0 20px rgba(220, 38, 38, 0.3);
        }
        
        .stats-label {
            font-size: 1.1rem;
            color: rgba(255, 255, 255, 0.9);
            font-weight: 600;
            margin-top: 0.5rem;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        
        /* Premium typography */
        h1, h2, h3 {
            color: white;
            font-weight: 800;
            text-shadow: 0 2px 10px rgba(0, 0, 0, 0.5);
        }
        
        .welcome-text {
            font-size: 1.2rem;
            color: rgba(255, 255, 255, 0.8);
            line-height: 1.6;
            text-shadow: 0 1px 5px rgba(0, 0, 0, 0.3);
            font-weight: 400;
        }
        
        /* Tab styling with red accents */
        .stTabs [data-baseweb="tab-list"] {
            background: rgba(0, 0, 0, 0.6);
            border-radius: 15px;
            padding: 0.5rem;
            border: 1px solid rgba(220, 38, 38, 0.2);
        }
        
        .stTabs [data-baseweb="tab-list"] button {
            background: transparent;
            border-radius: 10px;
            color: rgba(255, 255, 255, 0.7);
            font-weight: 600;
            transition: all 0.3s ease;
            border: 1px solid transparent;
        }
        
        .stTabs [data-baseweb="tab-list"] button[aria-selected="true"] {
            background: linear-gradient(45deg, #dc2626, #991b1b);
            color: white;
            box-shadow: 0 4px 15px rgba(220, 38, 38, 0.4);
            border-color: rgba(220, 38, 38, 0.5);
        }
        
        .stTabs [data-baseweb="tab-list"] button:hover {
            border-color: rgba(220, 38, 38, 0.3);
            background: rgba(220, 38, 38, 0.1);
        }
        
        /* Calendar styling */
        .fc {
            background: rgba(0, 0, 0, 0.4);
            border-radius: 15px;
            padding: 1rem;
            border: 1px solid rgba(220, 38, 38, 0.2);
        }
        
        .fc-toolbar-title {
            color: white !important;
            font-weight: 700 !important;
        }
        
        .fc-button-primary {
            background: linear-gradient(45deg, #dc2626, #991b1b) !important;
            border-color: #dc2626 !important;
        }
        
        .fc-button-primary:hover {
            background: linear-gradient(45deg, #ef4444, #dc2626) !important;
        }
        
        /* Sidebar content */
        .sidebar-content {
            color: white;
        }
        
        .sidebar-content h3 {
            color: #dc2626;
            font-weight: 700;
        }
        
        /* Input styling with red accents */
        .stSelectbox > div > div {
            background: rgba(0, 0, 0, 0.6);
            border: 1px solid rgba(220, 38, 38, 0.3);
            border-radius: 10px;
            color: white;
        }
        
        .stTextInput > div > div > input {
            background: rgba(0, 0, 0, 0.6);
            border: 1px solid rgba(220, 38, 38, 0.3);
            border-radius: 10px;
            color: white;
        }
        
        .stTextInput > div > div > input:focus {
            border-color: #dc2626;
            box-shadow: 0 0 10px rgba(220, 38, 38, 0.3);
        }
        
        /* Loading animations */
        .loading-spinner {
            border: 3px solid rgba(255, 255, 255, 0.2);
            border-radius: 50%;
            border-top: 3px solid #dc2626;
            width: 30px;
            height: 30px;
            animation: redSpin 1s linear infinite;
            margin: 0 auto;
        }
        
        @keyframes redSpin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        
        /* Button overrides for Streamlit */
        .stButton > button {
            background: linear-gradient(45deg, #dc2626, #991b1b);
            color: white;
            border: none;
            border-radius: 8px;
            font-weight: 600;
            transition: all 0.3s ease;
            box-shadow: 0 4px 15px rgba(220, 38, 38, 0.3);
        }
        
        .stButton > button:hover {
            background: linear-gradient(45deg, #ef4444, #dc2626);
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(220, 38, 38, 0.4);
        }
        
        /* Success, error, and info message styling */
        .stSuccess {
            background: rgba(0, 0, 0, 0.6);
            border-left: 4px solid #dc2626;
            color: white;
        }
        
        .stError {
            background: rgba(127, 29, 29, 0.3);
            border-left: 4px solid #7f1d1d;
            color: white;
        }
        
        .stInfo {
            background: rgba(0, 0, 0, 0.6);
            border-left: 4px solid #dc2626;
            color: white;
        }
        
        .stWarning {
            background: rgba(185, 28, 28, 0.3);
            border-left: 4px solid #b91c1c;
            color: white;
        }
        
        /* Expandar styling */
        .streamlit-expanderHeader {
            background: rgba(0, 0, 0, 0.4);
            border: 1px solid rgba(220, 38, 38, 0.3);
            color: white;
        }
        
        .streamlit-expanderContent {
            background: rgba(0, 0, 0, 0.2);
            border: 1px solid rgba(220, 38, 38, 0.2);
        }
        
        /* Responsive design */
        @media (max-width: 768px) {
            .glass-card {
                padding: 1rem;
                margin: 0.5rem 0;
            }
            
            .stats-number {
                font-size: 2rem;
            }
            
            .employee-avatar {
                width: 50px;
                height: 50px;
                font-size: 1.2rem;
            }
        }
        
        /* Special red glow effects */
        .red-glow {
            box-shadow: 0 0 20px rgba(220, 38, 38, 0.5);
        }
        
        .red-glow:hover {
            box-shadow: 0 0 30px rgba(220, 38, 38, 0.7);
        }
    </style>
  """)

st.header("Team Leave Calendar")
            # You can enhance this to draw events on a calendar from the DB
            # This part requires a calendar component like streamlit-calendar
            # For now, we'll just list the approved leaves.
st.info("Calendar view shows all approved leaves.")
approved_leaves = get_team_leaves(status_filter=["Approved"])
            
events = []
for leave in approved_leaves:
    events.append({
                    "title": f"{leave["employee_name"]} - {leave["leave_type"]}",
                    "start": leave["start_date"],
                    "end": leave["end_date"],
        })
            
            # If you have streamlit_calendar installed
try:
    from streamlit_calendar import calendar
    calendar(events=events)
except ImportError:
    st.write(events)

# Placeholder for LEAVE_POLICIES if not defined elsewhere
LEAVE_POLICIES = {
    "Annual": {}, "Sick": {}, "Maternity": {}, 
    "Paternity": {}, "Study": {}, "Compassionate": {}, "Unpaid": {}
}    
