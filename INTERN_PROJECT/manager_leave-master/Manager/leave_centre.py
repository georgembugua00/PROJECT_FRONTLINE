import streamlit as st
from datetime import date, timedelta, datetime
import sqlite3
import pandas as pd
import os

# Get the base directory where this script is located
base_dir = os.path.dirname(os.path.abspath(__file__))

# Go one level up to reach INTERN_PROJECT from human_resource
project_dir = os.path.dirname(base_dir)

# Build the path to leave_management.db
DB_NAME = os.path.join(project_dir, 'leave_management.db')
DB_PATH = "/Users/danielwanganga/Documents/GitHub/PROJECT_FRONTLINE/INTERN_PROJECT/leave_management.db"

def init_db():
    """Initializes and returns a connection to the SQLite database."""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row  # This allows accessing columns by name (e.g., row['column_name'])
        return conn
    except sqlite3.Error as e:
        st.error(f"Error connecting to database: {e}")
        return None


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
    """Fetches all pending leave requests from the 'leave_entries' table."""
    conn = init_db()
    pending_leaves = []
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, leave_id, employee_name, leave_type, start_date, end_date, description, status
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
    """Fetches all approved leave requests from the 'leave_entries' table."""
    conn = init_db()
    approved_leaves = []
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, leave_id, employee_name, leave_type, start_date, end_date, description, status
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
            query_sql = "SELECT id, leave_id, employee_name, leave_type, start_date, end_date, description, status, decline_reason, recall_reason FROM leave_entries WHERE 1=1"
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
    """Updates the status of a leave request in 'leave_entries' table."""
    if not leave_request_id:
        return False, "Invalid leave ID"
        
    conn = init_db()
    if conn:
        try:
            cursor = conn.cursor()
            
            # First, check if the record exists
            cursor.execute("SELECT id FROM leave_entries WHERE id = ?", (leave_request_id,))
            existing_record = cursor.fetchone()
            
            if not existing_record:
                return False, f"Leave request with ID {leave_request_id} not found."
            
            update_sql = "UPDATE leave_entries SET status = ?"
            params = [new_status]

            if new_status == "Declined":
                update_sql += ", decline_reason = ?, recall_reason = NULL"
                params.append(reason)
            elif new_status == "Recalled":
                update_sql += ", recall_reason = ?, decline_reason = NULL"
                params.append(reason)
            elif new_status == "Approved":
                update_sql += ", decline_reason = NULL, recall_reason = NULL"
            
            update_sql += " WHERE id = ?"
            params.append(leave_request_id)

            cursor.execute(update_sql, tuple(params))
            conn.commit()

            if cursor.rowcount > 0:
                return True, f"Leave status updated to {new_status}"
            else:
                return False, "Failed to update leave status (no rows affected)."
        except sqlite3.Error as e:
            return False, f"Error updating leave status: {str(e)}"
        finally:
            conn.close()
    return False, "Database connection failed."

# --- Leave Policies & UI elements ---
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
        color: #4caf50;
        font-size: 1.1em;
    }
    .stButton>button {
        background-color: #F44336;
        color: white;
        border-radius: 5px;
        padding: 10px 20px;
        font-size: 16px;
        border: none;
        cursor: pointer;
        transition: background-color 0.3s ease;
    }
    .stButton>button:hover {
        background-color: #4caf50;
    }
    .stButton>button[key*="decline"] {
        background-color: #4caf50;
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
        # Use the primary key 'id' for database operations
        leave_primary_id = leave["id"]
        leave_id_display = leave["leave_id"]  # For display purposes
        employee_name = leave["employee_name"]
        leave_type = leave["leave_type"]
        start_date = leave["start_date"]
        end_date = leave["end_date"]
        description = leave["description"]

        with st.expander(f"Request from {employee_name} ({leave_type}) - {start_date} to {end_date}", expanded=True):
            st.write(f"**Employee:** {employee_name}")
            st.write(f"**Leave ID:** {leave_id_display}")
            st.write(f"**Leave Type:** {leave_type}")
            st.write(f"**Dates:** {start_date} to {end_date}")
            st.write(f"**Reason:** {description if description else 'No description provided.'}")

            col1, col2 = st.columns([1, 1])
            with col1:
                if st.button("✅ Approve", key=f"approve_{leave_primary_id}"):
                    success, message = update_leave_status(leave_primary_id, "Approved")
                    if success:
                        st.success(f"Leave for {employee_name} approved.")
                        st.rerun()
                    else:
                        st.error(f"Failed to approve leave: {message}")
            
            with col2:
                # Use session state to manage decline reason input visibility
                decline_key = f"show_decline_{leave_primary_id}"
                if decline_key not in st.session_state:
                    st.session_state[decline_key] = False
                
                if st.button("❌ Decline", key=f"decline_btn_{leave_primary_id}"):
                    st.session_state[decline_key] = True
                    st.rerun()
                
                if st.session_state.get(decline_key, False):
                    decline_reason = st.text_input("Reason for declining:", key=f"decline_reason_{leave_primary_id}")
                    
                    col_confirm, col_cancel = st.columns([1, 1])
                    with col_confirm:
                        if st.button("Confirm Decline", key=f"confirm_decline_{leave_primary_id}"):
                            if decline_reason.strip():
                                success, message = update_leave_status(leave_primary_id, "Declined", reason=decline_reason)
                                if success:
                                    st.error(f"Leave for {employee_name} declined.")
                                    st.session_state[decline_key] = False  # Reset state
                                    st.rerun()
                                else:
                                    st.error(f"Failed to decline leave: {message}")
                            else:
                                st.warning("A reason is required to decline a request.")
                    
                    with col_cancel:
                        if st.button("Cancel", key=f"cancel_decline_{leave_primary_id}"):
                            st.session_state[decline_key] = False
                            st.rerun()

def approved_leaves_for_recall_view():
    st.header("Approved Leaves (for Recall)")
    approved_leaves = get_approved_leaves()

    if not approved_leaves:
        st.info("No approved leaves currently.")
        return

    for leave in approved_leaves:
        # Use the primary key 'id' for database operations
        leave_primary_id = leave["id"]
        leave_id_display = leave["leave_id"]
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
            st.error(f"⚠️ Invalid date format in leave ID {leave_id_display} for {employee_name}: {start_date_str} to {end_date_str}")
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
            st.write(f"**Leave ID:** {leave_id_display}")
            st.write(f"**Leave Type:** {leave_type}")
            st.write(f"**Dates:** {start_date_str} to {end_date_str}")
            st.write(f"**Reason:** {description if description else 'No description provided.'}")
            st.write(f"**Days Remaining:** {days_left}")

            # Use session state to manage recall reason input
            recall_key = f"show_recall_{leave_primary_id}"
            if recall_key not in st.session_state:
                st.session_state[recall_key] = False
            
            if st.button("↩️ Recall Leave", key=f"recall_btn_{leave_primary_id}"):
                st.session_state[recall_key] = True
                st.rerun()
            
            if st.session_state.get(recall_key, False):
                recall_reason = st.text_input("Reason for recall:", value="Operational Need", key=f"recall_reason_{leave_primary_id}")
                
                col_confirm, col_cancel = st.columns([1, 1])
                with col_confirm:
                    if st.button("Confirm Recall", key=f"confirm_recall_{leave_primary_id}"):
                        if days_left > 3:
                            success, message = update_leave_status(leave_primary_id, "Recalled", reason=recall_reason)
                            if success:
                                st.warning(f"Leave for {employee_name} has been recalled due to {recall_reason}.")
                                st.session_state[recall_key] = False  # Reset state
                                st.rerun()
                            else:
                                st.error(f"Failed to recall leave: {message}")
                        else:
                            st.error(f"Cannot recall leave for {employee_name}. Less than 3 days ({days_left} days) remaining or leave has ended.")
                
                with col_cancel:
                    if st.button("Cancel", key=f"cancel_recall_{leave_primary_id}"):
                        st.session_state[recall_key] = False
                        st.rerun()

def team_leaves_dashboard_view():
    st.header("Team Leave Dashboard")

    all_employees = ["All Team Members"] + get_all_employees_from_db()
    
    col1, col2, col3 = st.columns(3)
    with col1:
        selected_employee = st.selectbox("Filter by Employee", all_employees)
    with col2:
        selected_status = st.multiselect("Filter by Status", ["Pending", "Approved", "Declined", "Withdrawn", "Recalled"], default=["Pending", "Approved"])
    with col3:
        all_leave_types = list(LEAVE_TYPE_MAPPING.keys())
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
            "Leave ID": leave["leave_id"],
            "Employee": leave["employee_name"],
            "Leave Type": leave["leave_type"],
            "Start Date": leave["start_date"],
            "End Date": leave["end_date"],
            "Status": leave["status"],
            "Description": leave["description"] if leave["description"] else "N/A",
            "Decline Reason": leave["decline_reason"] if leave["decline_reason"] else "N/A",
            "Recall Reason": leave["recall_reason"] if leave["recall_reason"] else "N/A"
        })

    # Display results in a table for better readability
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