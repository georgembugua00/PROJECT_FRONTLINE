import streamlit as st
import sqlite3
from datetime import date, timedelta, datetime

# --- SQLite Database Configuration ---
DB_NAME = "INTERN_PROJECT/leave_management.db"

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
    IMPORTANT: Added 'status' column to 'leave' table and adjusted
    'decline_reason'/'recall_reason' to default to empty string, as they are NOT NULL.
    """
    conn = init_db()
    if conn:
        try:
            cursor = conn.cursor()

            # 1. Create employee_table_rows (formerly employee_table)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS "employee_table_rows" (
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

            # 2. Create leave (formerly leave_leave)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS "leave" (
                    "id"	INTEGER PRIMARY KEY AUTOINCREMENT,
                    "employee_id"   TEXT NOT NULL, -- Links to employee_table_rows.uuid
                    "employee_name"	TEXT NOT NULL,
                    "leave_type"	TEXT NOT NULL,
                    "start_date"	TEXT NOT NULL,
                    "end_date"	TEXT NOT NULL,
                    "description"	TEXT, -- Your schema had NOT NULL, but it's often nullable. If NOT NULL is strict, change to TEXT NOT NULL.
                    "attachment"	INTEGER DEFAULT 0, -- BOOLEAN is INTEGER in SQLite (0 or 1)
                    "status"    TEXT DEFAULT 'Pending', -- CRITICAL ADDITION: Was missing from your provided 'leave' schema
                    "decline_reason"	TEXT DEFAULT '', -- Your schema was NOT NULL; using default empty string
                    "recall_reason"	TEXT DEFAULT '', -- Your schema was NOT NULL; using default empty string
                    FOREIGN KEY ("employee_id") REFERENCES "employee_table_rows"("uuid")
                );
            """)

            # 3. Create leave_entitlements
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS "leave_entitlements (1)" (
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
            # st.success("Database tables created or already exist.") # Only for debugging setup
        except sqlite3.Error as e:
            st.error(f"Error creating tables: {e}")
        finally:
            conn.close()

# Call create_tables once when the application starts
create_tables()

# --- CRUD Operations (SQLite3 versions) ---

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

def get_latest_leave_entry_for_employee_by_id(employee_uuid):
    """
    Get the latest leave entry for a specific employee by employee UUID.
    
    Args:
        employee_uuid (str): The UUID of the employee
        
    Returns:
        dict or None: The latest leave entry for the employee, or None if not found
    """
    conn = init_db()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, leave_id, leave_type, start_date, end_date, description, status, decline_reason, recall_reason
                FROM leave_entries
                WHERE leave_id = ?
                ORDER BY start_date DESC, id DESC -- Order by ID too for deterministic "latest"
                LIMIT 1
            """, (employee_uuid,))
            leave_entry = cursor.fetchone()
            if leave_entry:
                return dict(leave_entry)
            return None
        except sqlite3.Error as e:
            st.error(f"Error fetching latest leave entry for employee: {str(e)}")
            return None
        finally:
            conn.close()
    return None

def apply_for_leave(employee_uuid, employee_name, leave_type, start_date, end_date, description, attachment=None):
    """Adds a new leave application to the leave table."""
    conn = init_db()
    if conn:
        try:
            # Ensure dates are in ISO format for SQLite storage
            if isinstance(start_date, date):
                start_date_str = start_date.isoformat()
            else: # Assume string, try to convert
                start_date_str = datetime.fromisoformat(start_date).date().isoformat()

            if isinstance(end_date, date):
                end_date_str = end_date.isoformat()
            else: # Assume string, try to convert
                end_date_str = datetime.fromisoformat(end_date).date().isoformat()

            # SQLite stores booleans as 0 (False) or 1 (True)
            attachment_int = 1 if attachment else 0

            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO leave_entries (leave_id, employee_name, leave_type, start_date, end_date, description, attachment, status, decline_reason, recall_reason)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (employee_uuid, employee_name, leave_type, start_date_str, end_date_str, description, attachment_int, "Pending", "", ""))
            conn.commit()
            return True, "Leave request submitted successfully!"
        except sqlite3.Error as e:
            return False, f"Error submitting leave request: {str(e)}"
        finally:
            conn.close()
    return False, "Database connection failed."

def get_leave_history(employee_uuid):
    """Fetches the leave history for a specific employee from leave table."""
    conn = init_db()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, leave_type, start_date, end_date, description, status, decline_reason, recall_reason
                FROM leave_entries
                WHERE leave_id = ?
                ORDER BY start_date DESC
            """, (employee_uuid,))
            leave_history = cursor.fetchall()
            return [dict(row) for row in leave_history]
        except sqlite3.Error as e:
            st.error(f"Error fetching leave history: {str(e)}")
            return []
        finally:
            conn.close()
    return []

def get_pending_leaves_for_employee(employee_uuid):
    """Fetches pending leave requests for a specific employee from leave table."""
    conn = init_db()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, leave_id, employee_name, leave_type, start_date, end_date, description
                FROM leave_entries
                WHERE leave_id = ? AND status = 'Pending'
            """, (employee_uuid,))
            pending_leaves = cursor.fetchall()
            return [dict(row) for row in pending_leaves]
        except sqlite3.Error as e:
            st.error(f"Error fetching pending leaves: {str(e)}")
            return []
        finally:
            conn.close()
    return []

def update_leave_status(leave_request_id, new_status, reason=""): # Default reason to empty string
    """Updates the status of a leave request in leave table using its 'id'."""
    if not leave_request_id:
        return False, "Invalid leave ID"
        
    conn = init_db()
    if conn:
        try:
            cursor = conn.cursor()
            update_sql = "UPDATE leave_entries SET status = ?"
            params = [new_status]

            if new_status == "Declined":
                update_sql += ", decline_reason = ?, recall_reason = ''" # Clear recall_reason
                params.append(reason)
            elif new_status in ["Recalled", "Withdrawn"]:
                update_sql += ", recall_reason = ?, decline_reason = ''" # Clear decline_reason
                params.append(reason)
            elif new_status == "Approved": # Clear both reasons if approved
                update_sql += ", decline_reason = '', recall_reason = ''"
            
            update_sql += " WHERE id = ?" # Use 'id' from leave table
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

def get_employee_leave_entitlements(employee_uuid):
    """Fetches leave entitlements for a given employee from leave_entitlements table."""
    conn = init_db()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM leave_entitlements_data WHERE leave_id = ?", (employee_uuid,))
            entitlements = cursor.fetchone()
            if entitlements:
                return dict(entitlements)
            return None
        except sqlite3.Error as e:
            st.error(f"Error fetching employee leave entitlements: {str(e)}")
            return None
        finally:
            conn.close()
    return None

def get_employee_used_leave(employee_uuid, leave_type=None):
    """Calculates total used leave days for an employee, optionally by type, from leave table."""
    conn = init_db()
    if conn:
        try:
            cursor = conn.cursor()
            query_sql = "SELECT start_date, end_date FROM leave_entries WHERE leave_id = ? AND status = 'Approved'"
            params = [employee_uuid]

            if leave_type:
                query_sql += " AND leave_type = ?"
                params.append(leave_type)

            cursor.execute(query_sql, tuple(params))
            approved_leaves = cursor.fetchall()
            used_days = 0
            if approved_leaves:
                for record in approved_leaves:
                    start = datetime.fromisoformat(record['start_date']).date()
                    end = datetime.fromisoformat(record['end_date']).date()
                    used_days += (end - start).days + 1
            return int(used_days)
        except sqlite3.Error as e:
            st.error(f"Error calculating used leave: {str(e)}")
            return 0
        finally:
            conn.close()
    return 0

def withdraw_leave(leave_id, recall_reason=None): # Renamed recall_leave to recall_reason for consistency
    """Marks a leave request as Withdrawn in leave table with an optional reason."""
    return update_leave_status(leave_id, "Withdrawn", recall_reason)


# --- Leave Policies - Now dynamically fetched or derived (leave_entitlements table) ---
LEAVE_TYPE_MAPPING = {
    "Annual": "annual_leave",
    "Sick": "sick_leave",
    "Maternity": "maternity_leave_days",
    "Paternity": "paternity_leave_days",
    "Study": "compensation_leave", # Assuming study maps to compensation leave days
    "Compensation": "compensation_leave", # Explicitly add for clarity
    "Compassionate": "compensation_leave", # Assuming compassionate maps to compensation leave days
    "Unpaid": None
}

st.set_page_config(layout="wide")

# --- REPLACE HARDCODED LOGIC WITH PROPER USER AUTHENTICATION ---
# Check if user is logged in via the SSO system
if not st.session_state.get('logged_in', False):
    st.error("Please log in through the main application to access the leave management system.")
    st.stop()

# Get current user information from session state (set by main.py after SSO login)
logged_in_user_id = st.session_state.get('user_id')  # This is the AUUID from employee_table_rows
logged_in_full_name = st.session_state.get('full_name')
logged_in_username = st.session_state.get('username')  # Email
logged_in_user_role = st.session_state.get('user_role')  # Sub_Department

# Verify user exists in database
if logged_in_user_id:
    # Use employee_uuid instead of employee_id as per our functions
    employee_data = get_employee_by_id(logged_in_user_id) 
    if not employee_data:
        st.error("Employee data not found in database. Please contact administrator.")
        st.stop()
    
    # Set session state variables for consistency with original code
    st.session_state['current_employee_id'] = logged_in_user_id # Using 'id' for consistency with internal app logic
    st.session_state['current_employee_name'] = employee_data.get('First_Name', '')
else:
    st.error("No user ID found in session. Please log in again.")
    st.stop()

# --- MAIN APPLICATION LAYOUT ---
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
    .stButton>button[key*="withdraw"] {
        background-color: #e74c3c;
    }
    .stButton>button[key*="withdraw"]:hover {
        background-color: #c0392b;
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
    <h1>📝 Employee Leave Portal</h1>
    <p style="margin: 0; opacity: 0.9;">Apply, withdraw, and track your leave requests</p>
</div>
""")

# Display current user information
st.info(f"Welcome, **{logged_in_full_name}**! ({logged_in_username})")

# --- Sidebar Alert for Leave Status Updates ---
try:
    st.sidebar.header("Your Latest Leave Status")
    user_latest_leave = get_latest_leave_entry_for_employee_by_id(logged_in_user_id)
    
    if user_latest_leave:
        # Note: In SQLite, date columns are TEXT. Convert if needed for display logic.
        leave_type = user_latest_leave.get("leave_type")
        start_date = user_latest_leave.get("start_date")
        end_date = user_latest_leave.get("end_date")
        status = user_latest_leave.get("status")
        decline_reason = user_latest_leave.get("decline_reason")
        recall_reason = user_latest_leave.get("recall_reason") # Corrected column name

        st.sidebar.markdown(f"**Latest Leave Request**")
        if status == "Declined":
            st.sidebar.error(f"Declined: **{leave_type}** Leave from {start_date} to {end_date}. Reason: {decline_reason}")
        elif status == "Recalled":
            st.sidebar.warning(f"Recalled: **{leave_type}** Leave from {start_date} to {end_date}. Reason: {recall_reason}")
        elif status == "Approved":
            st.sidebar.success(f"Approved: **{leave_type}** Leave from {start_date} to {end_date}")
        elif status == "Pending":
            st.sidebar.info(f"Pending: **{leave_type}** Leave from {start_date} to {end_date}.")
        elif status == "Withdrawn":
            st.sidebar.info(f"Withdrawn: **{leave_type}** Leave from {start_date} to {end_date}. Reason: {recall_reason}")
    else:
        st.sidebar.info("No leave entries found for your profile yet.")
except Exception as e:
    st.sidebar.error(f"Error loading leave status: {str(e)}")

tabs = st.tabs(["Apply Leave", "Withdraw Leave", "Leave History", "Leave Planner"])

# Apply Leave Tab
with tabs[0]:
    st.header("Apply for Leave")

    # Use 'current_employee_id' which maps to employee_table_rows.uuid
    employee_uuid = st.session_state.get('current_employee_id') 
    employee_name = st.session_state.get('current_employee_name')

    if employee_uuid:
        leave_type = st.selectbox("Select Leave Type", list(LEAVE_TYPE_MAPPING.keys()), key="apply_leave_type")
        start = st.date_input("Start Date", min_value=date.today(), key="apply_start_date")
        end = st.date_input("End Date", min_value=start, key="apply_end_date")
        description = st.text_area("Reason for Leave", key="apply_description")

        attachment_required = leave_type in ["Sick", "Maternity", "Paternity", "Compassionate"]
        attachment = st.file_uploader("Upload Attachment (if required)", type=['pdf', 'jpg', 'png'], key="apply_attachment") if attachment_required else None

        leave_days_requested = (end - start).days + 1

        entitlements = get_employee_leave_entitlements(employee_uuid) # Pass UUID
        leave_column = LEAVE_TYPE_MAPPING.get(leave_type)

        if entitlements and leave_column:
            entitled_days = entitlements.get(leave_column, 0)
            used_days = get_employee_used_leave(employee_uuid, leave_type) # Pass UUID
            remaining_days = entitled_days - used_days - leave_days_requested

            st.info(f"**Entitled Days ({leave_type})**: {entitled_days}")
            st.warning(f"**Used Days**: {used_days}")
            st.info(f"**Applying For**: {leave_days_requested} days")
            st.success(f"**Remaining After Application**: {remaining_days}")

            if st.button("Apply Leave", key="apply_leave_submit"):
                if remaining_days >= 0:
                    success, message = apply_for_leave(employee_uuid, employee_name, leave_type, start, end, description, bool(attachment)) # Pass UUID
                    if success:
                        st.success(message)
                        st.rerun()
                    else:
                        st.error(message)
                else:
                    st.error(f"Insufficient leave balance. You only have {max(0, entitled_days - used_days)} days remaining for {leave_type} leave.")

        elif leave_type == "Unpaid":
            st.info("Unpaid leave has no entitlement cap but requires approval.")
            if st.button("Apply for Unpaid Leave", key="apply_unpaid_leave"):
                success, message = apply_for_leave(employee_uuid, employee_name, leave_type, start, end, description, bool(attachment)) # Pass UUID
                if success:
                    st.success(message)
                    st.rerun()
                else:
                    st.error(message)
        else:
            st.warning(f"No entitlement policy found for {leave_type}. Proceeding without entitlement check.")
            if st.button("Apply Leave Without Entitlement Check", key="apply_leave_no_entitlement"):
                success, message = apply_for_leave(employee_uuid, employee_name, leave_type, start, end, description, bool(attachment)) # Pass UUID
                if success:
                    st.success("Leave applied successfully without entitlement check.")
                    st.rerun()
                else:
                    st.error(message)

# Withdraw Leave Tab
with tabs[1]:
    st.header("Withdraw Leave Request")
    employee_uuid_for_withdrawal = st.session_state.get('current_employee_id')

    if employee_uuid_for_withdrawal:
        leaves_to_withdraw = get_pending_leaves_for_employee(employee_uuid_for_withdrawal) # Pass UUID

        if not leaves_to_withdraw:
            st.info("No pending leave requests to withdraw for your profile.")
        else:
            for leave in leaves_to_withdraw:
                # 'id' is the primary key for the 'leave' table
                leave_id = leave['id'] 
                with st.expander(f"{leave['leave_type']} Leave: {leave['start_date']} to {leave['end_date']}"):
                    st.markdown(f"**Reason**: {leave['description']}")
                    withdraw_reason = st.selectbox("Reason for Withdrawal", ["Change of Plan", "Emergency", "Other"], key=f"withdraw_reason_{leave_id}")
                    if withdraw_reason == "Other":
                        withdraw_reason = st.text_area("Please Specify", key=f"withdraw_custom_{leave_id}")
                    if st.button("Withdraw", key=f"withdraw_btn_{leave_id}"):
                        # Pass leave_id (which is 'id' from leave) and the reason
                        success, message = withdraw_leave(leave_id, withdraw_reason) 
                        if success:
                            st.success(message)
                            st.rerun()
                        else:
                            st.error(message)

# Leave History Tab
with tabs[2]:
    st.header("Your Leave History")
    employee_uuid_for_history = st.session_state.get('current_employee_id')

    if employee_uuid_for_history:
        employee_leave_history = get_leave_history(employee_uuid_for_history) # Pass UUID
        if employee_leave_history:
            for hist_entry in employee_leave_history:
                leave_type_hist = hist_entry.get("leave_type")
                start_date_hist = hist_entry.get("start_date")
                end_date_hist = hist_entry.get("end_date")
                description_hist = hist_entry.get("description")
                status_hist = hist_entry.get("status")
                decline_reason_hist = hist_entry.get("decline_reason")
                recall_reason_hist = hist_entry.get("recall_reason") # Corrected column name

                status_display = f"({status_hist})"
                if status_hist == "Declined" and decline_reason_hist:
                    status_display += f" - Reason: {decline_reason_hist}"
                elif status_hist in ["Recalled", "Withdrawn"] and recall_reason_hist: # Grouped recalled and withdrawn
                    status_display += f" - Reason: {recall_reason_hist}"

                st.markdown(f"""
                <div style='border:1px solid #ddd; padding:10px; margin:10px; border-radius:5px;'>
                    <strong>{leave_type_hist} Leave</strong> {status_display}<br>
                    {start_date_hist} to {end_date_hist}<br>
                    <em>{description_hist if description_hist else 'No description'}</em>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("No leave history found for your profile.")

# Leave Planner Tab
with tabs[3]:
    st.header("AI-Powered Leave Planner 🧠")
    st.info("This feature helps you plan your leave and delegate tasks.")
    
    if logged_in_user_id:
        total_days = st.number_input("How many leave days do you want to use?", min_value=1, max_value=365, key="planner_total_days")
        spread_days = st.number_input("Over how many days should they be spread?", min_value=1, max_value=365, key="planner_spread_days")
        deadlines = st.text_area("List any important deadlines during that period", key="planner_deadlines")
        emergency_contact = st.text_input("Emergency Contact Person and Number", key="planner_emergency_contact")
        task_info = st.text_area("List any ongoing tasks or projects", key="planner_task_info")
        delegated_to = st.text_input("Who will pick up your tasks?", key="planner_delegated_to")
        notes = st.text_area("Any notes for task handover", key="planner_notes")
        events = st.text_input("Any events you're planning to attend?", key="planner_events")
        
        if st.button("Generate Plan", key="generate_plan_btn"):
            # Simple placeholder logic for the planner, as it's not database-driven
            leave_plan = {
                "start_date": str(date.today() + timedelta(days=2)),
                "end_date": str(date.today() + timedelta(days=1 + total_days + 1)),
                "days": total_days
            }
            delegation_plan = {
                "task": task_info,
                "delegate": delegated_to,
                "notes": notes
            }
            st.success("✅ Plan Generated")
            st.write("### 🗓️ Leave Schedule")
            st.json(leave_plan)
            st.write("### 🧾 Task Delegation")
            st.json(delegation_plan)

st.markdown("---")
st.html("""
<div style="text-align: center; color: #6b7280; padding: 1rem;">
    <p>Employee Leave Portal | Built with Streamlit and SQLite</p>
</div>
""")
