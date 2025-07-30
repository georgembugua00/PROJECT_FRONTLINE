import streamlit as st
from datetime import date, timedelta, datetime
import sqlite3
import pandas as pd # Still useful for DataFrame conversion

import pandas as pd
import sqlite3

conn = sqlite3.connect('leave_management.db')

employee_data = pd.read_csv("./employee_table.csv")
leave_entry_data = pd.read_csv("./data/leave_entries.csv")
leave_entitlements_data = pd.read_csv("./data/leave_entitlements_data.csv")

employee_data.to_sql(name="employee_table",con=conn,if_exists='replace',index=False)
leave_entry_data.to_sql(name="leave_entry",con=conn,if_exists='replace',index=False)
leave_entitlements_data.to_sql(name="leave_entitlements_data",con=conn,if_exists='replace',index=False)

table_names = conn.execute("SELECT name FROM sqlite_master WHERE type='table';").fetchall()
print(table_names)

leave_entitlement = conn.execute(("SELECT * FROM leave_entitlements_data")).fetchall()

leave_entry = conn.execute(("SELECT * FROM leave_entry")).fetchall()

print(leave_entry)

#print(leave_entitlement)

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
    """Fetches employee details by UUID from employee_table_rows."""
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
    """Fetches employee details by First_Name from employee_table_rows."""
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
                FROM leave_entry
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
                FROM leave_entry
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
            query_sql = "SELECT leave_id, employee_name, leave_type, start_date, end_date, description, status, decline_reason, recall_reason FROM leave_entry WHERE 1=1"
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
            update_sql = "UPDATE leave_entry SET status = ?"
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

# Main app structure with tabs for manager
tab1, tab2, tab3 = st.tabs(["Pending Requests", "Approved Leaves (Recall)", "Team Leave Dashboard"])

with tab1:
    pending_leaves_view()

with tab2:
    approved_leaves_for_recall_view()

with tab3:
    team_leaves_dashboard_view()

# Footer
st.markdown("---")
st.html("""
<div style="text-align: center; color: #6b7280; padding: 1rem;">
    <p>Leave Request Management System | Manager View | Built with Streamlit & SQLite</p>
</div>
""")
