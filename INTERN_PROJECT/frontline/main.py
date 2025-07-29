import streamlit as st
import sqlite3
import os
import datetime
from dotenv import load_dotenv

# Load environment variables (from .env or .streamlit/secrets.toml)
load_dotenv()

# ========== PAGE CONFIG ==========
st.set_page_config(
    page_title="Frontline Agent Portal",
    layout="wide",
    initial_sidebar_state="expanded",  # Ensure sidebar is expanded
)

# Database file path
DATABASE_PATH = "leave_management.db"

# Initialize SQLite database
    
 

def get_db_connection():
    """Get SQLite database connection."""
    return sqlite3.connect(DATABASE_PATH)

def authenticate_user(email, password):
    """Authenticate user with email and password from employee_table."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT uuid, AUUID, First_Name, Surname_Name, Email, Sub_Department, password
            FROM employee_table 
            WHERE Email = ?
        ''', (email,))
        
        employee = cursor.fetchone()
        conn.close()
        
        if employee:
            # In production, you should compare hashed passwords
            stored_password = employee[6]  # password is at index 6
            if stored_password == password:  # Simple comparison - use hashing in production
                return {
                    'uuid': employee[0],
                    'AUUID': employee[1],
                    'First_Name': employee[2],
                    'Surname_Name': employee[3],
                    'Email': employee[4],
                    'Sub_Department': employee[5],
                    'password': employee[6]
                }
        return None
    except Exception as e:
        st.error(f"Authentication error: {str(e)}")
        return None

def get_employee_by_name(employee_name):
    """Fetches employee details by name from SQLite."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT uuid, First_Name 
            FROM employee_table 
            WHERE First_Name = ?
        ''', (employee_name,))
        
        employee = cursor.fetchone()
        conn.close()
        
        if employee:
            return {'uuid': employee[0], 'First_Name': employee[1]}
        return None
    except Exception as e:
        st.error(f"Error fetching employee by name: {str(e)}")
        return None

def apply_for_leave(employee_id, leave_type, start_date, end_date, description, attachment):
    """Adds a new leave application to the SQLite database."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO leave_entries 
            (employee_id, leave_type, start_date, end_date, description, attachment, status)
            VALUES (?, ?, ?, ?, ?, ?, 'Pending')
        ''', (employee_id, leave_type, start_date.isoformat(), end_date.isoformat(), 
              description, bool(attachment)))
        
        conn.commit()
        conn.close()
        return True, "Leave request submitted successfully!"
    except Exception as e:
        return False, f"Error submitting leave request: {str(e)}"

def get_leave_history(employee_id):
    """Fetches the leave history for a specific employee from SQLite."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT leave_type, start_date, end_date, description, status, decline_reason, recall_reason
            FROM leave_entries 
            WHERE employee_id = ?
            ORDER BY start_date DESC
        ''', (employee_id,))
        
        history = cursor.fetchall()
        conn.close()
        return history
    except Exception as e:
        st.error(f"Error fetching leave history: {str(e)}")
        return []

def get_all_pending_leaves():
    """Fetches all leave requests with a 'Pending' status for the manager from SQLite."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT l.AUUID, l.employee_id, l.leave_type, l.start_date, l.end_date, l.description, e.First_Name
            FROM leave_entries l
            JOIN employee_table e ON l.employee_id = e.uuid
            WHERE l.status = 'Pending'
        ''')
        
        rows = cursor.fetchall()
        conn.close()
        
        pending_leaves = []
        for row in rows:
            pending_leaves.append({
                "id": row[0],  # AUUID
                "employee_name": row[6],  # First_Name
                "leave_type": row[2],
                "start_date": row[3],
                "end_date": row[4],
                "description": row[5]
            })
        return pending_leaves
    except Exception as e:
        st.error(f"Error fetching pending leaves: {str(e)}")
        return []

def get_approved_leaves():
    """Fetches all leave requests with an 'Approved' status from SQLite."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT l.AUUID, l.employee_id, l.leave_type, l.start_date, l.end_date, l.description, e.First_Name
            FROM leave_entries l
            JOIN employee_table e ON l.employee_id = e.uuid
            WHERE l.status = 'Approved'
        ''')
        
        rows = cursor.fetchall()
        conn.close()
        
        approved_leaves = []
        for row in rows:
            approved_leaves.append({
                "id": row[0],  # AUUID
                "employee_name": row[6],  # First_Name
                "leave_type": row[2],
                "start_date": row[3],
                "end_date": row[4],
                "description": row[5]
            })
        return approved_leaves
    except Exception as e:
        st.error(f"Error fetching approved leaves: {str(e)}")
        return []

def update_leave_status(leave_id, new_status, reason=None):
    """Updates the status of a leave request in SQLite."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        if new_status == "Declined":
            cursor.execute('''
                UPDATE leave_entries 
                SET status = ?, decline_reason = ?
                WHERE employee_id = ?
            ''', (new_status, reason, leave_id))
        elif new_status == "Recalled":
            cursor.execute('''
                UPDATE leave_entries 
                SET status = ?, recall_reason = ?
                WHERE employee_id = ?
            ''', (new_status, reason, leave_id))
        elif new_status == "Withdrawn":
            cursor.execute('''
                UPDATE leave_entries 
                SET status = ?, recall_reason = ?
                WHERE employee_id = ?
            ''', (new_status, reason, leave_id))
        else:
            cursor.execute('''
                UPDATE off_roll_leave 
                SET status = ?
                WHERE employee_id = ?
            ''', (new_status, leave_id))
        
        conn.commit()
        affected_rows = cursor.rowcount
        conn.close()
        
        if affected_rows > 0:
            return True, f"Leave status updated to {new_status}"
        return False, "Failed to update leave status"
    except Exception as e:
        return False, f"Error updating leave status: {str(e)}"

def get_team_leaves(status_filter=None, leave_type_filter=None, employee_filter=None):
    """Fetches all team leaves with optional filters for the manager's dashboard from SQLite."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        query = '''
            SELECT l.employee_id, l.leave_type, l.start_date, l.end_date, l.status, 
                   l.description, l.decline_reason, e.First_Name
            FROM leave_entries l
            JOIN employee_table e ON l.employee_id = e.uuid
            WHERE 1=1
        '''
        params = []
        
        if status_filter:
            placeholders = ','.join(['?' for _ in status_filter])
            query += f' AND l.status IN ({placeholders})'
            params.extend(status_filter)
        
        if leave_type_filter:
            placeholders = ','.join(['?' for _ in leave_type_filter])
            query += f' AND l.leave_type IN ({placeholders})'
            params.extend(leave_type_filter)
        
        if employee_filter and employee_filter != "All Team Members":
            query += ' AND e.First_Name = ?'
            params.append(employee_filter)
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()
        
        leaves = []
        for row in rows:
            leaves.append({
                "employee_name": row[7],  # First_Name
                "leave_type": row[1],
                "start_date": row[2],
                "end_date": row[3],
                "status": row[4],
                "description": row[5],
                "decline_reason": row[6]
            })
        return leaves
    except Exception as e:
        st.error(f"Error fetching team leaves: {str(e)}")
        return []

def get_all_employees_from_db():
    """Gets a unique list of all employees from the employees table in SQLite."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT DISTINCT First_Name FROM employee_table ORDER BY First_Name')
        rows = cursor.fetchall()
        conn.close()
        
        employees = [row[0] for row in rows]
        return employees
    except Exception as e:
        st.error(f"Error fetching employees: {str(e)}")
        return []

def get_all_leaves():
    """Fetches all leave records from SQLite, joining with employee names."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT l.AUUID, l.leave_type, l.start_date, l.end_date, l.description, l.status, e.First_Name
            FROM leave_entries l
            JOIN employee_table e ON l.employee_id = e.uuid
        ''')
        
        rows = cursor.fetchall()
        conn.close()
        
        leaves = []
        for row in rows:
            leaves.append({
                "id": row[0],
                "name": row[6],  # First_Name
                "type": row[1],
                "start": row[2],
                "end": row[3],
                "description": row[4],
                "status": row[5]
            })
        return leaves
    except Exception as e:
        st.error(f"Error fetching all leaves: {str(e)}")
        return []

def withdraw_leave(leave_id, recall_reason=None):
    """Marks a leave request as Withdrawn in SQLite with an optional reason."""
    return update_leave_status(leave_id, "Withdrawn", recall_reason)

def get_latest_leave_entry():
    """Fetches the details of the most recently added leave entry from SQLite."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT l.leave_type, l.start_date, l.end_date, l.description, 
                   l.status, l.decline_reason, l.recall_reason, e.First_Name
            FROM leave_entries l
            JOIN employee_table e ON l.employee_id = e.uuid
            ORDER BY l.id DESC
            LIMIT 1
        ''')
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return {
                "employee_name": row[7],  # First_Name
                "leave_type": row[0],
                "start_date": row[1],
                "end_date": row[2],
                "description": row[3],
                "status": row[4],
                "decline_reason": row[5],
                "recall_reason": row[6]
            }
        return None
    except Exception as e:
        st.error(f"Error fetching latest leave entry: {str(e)}")
        return None

def get_employee_leave_entitlements(employee_id):
    """Fetches leave entitlements for a given employee from SQLite."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM leave_entitlements_data WHERE employee_id = ?', (employee_id,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return {
                'id': row[0],
                'employee_id': row[1],
                'annual_leave': row[2],
                'sick_leave': row[3],
                'maternity_leave': row[4],
                'paternity_leave': row[5],
                'compassionate_leave': row[6]
            }
        return None
    except Exception as e:
        st.error(f"Error fetching employee leave entitlements: {str(e)}")
        return None

def get_employee_used_leave(employee_id, leave_type=None):
    """Calculates total used leave days for an employee, optionally by type, from SQLite."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        query = '''
            SELECT start_date, end_date 
            FROM leave_entries 
            WHERE employee_id = ? AND status = 'Approved'
        '''
        params = [employee_id]
        
        if leave_type:
            query += ' AND leave_type = ?'
            params.append(leave_type)
        
        cursor.execute(query, params)
        records = cursor.fetchall()
        conn.close()
        
        used_days = 0
        for record in records:
            start = datetime.datetime.fromisoformat(record[0])
            end = datetime.datetime.fromisoformat(record[1])
            used_days += (end - start).days + 1  # +1 to include start and end day
        
        return int(used_days)
    except Exception as e:
        st.error(f"Error calculating used leave: {str(e)}")
        return 0

# Initialize database on startup

# ========== SIMPLE LOGIN FORM ==========
def simple_login_page():
    """Display simple login form."""
    st.title("🔐 Frontline Agent Portal")
    st.markdown("### Please sign in to continue")
    
    with st.form("login_form"):
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col2:
            email = st.text_input("📧 Email", placeholder="Enter your email address")
            password = st.text_input("🔒 Password", type="password", placeholder="Enter your password")
            
            login_button = st.form_submit_button("Sign In", use_container_width=True)
    
    if login_button:
        if email and password:
            with st.spinner("Authenticating..."):
                employee_data = authenticate_user(email, password)
                
                if employee_data:
                    # Set session state for successful login
                    st.session_state.logged_in = True
                    st.session_state.user_id = employee_data['uuid']
                    st.session_state.full_name = f"{employee_data.get('First_Name', '')} {employee_data.get('Surname_Name', '')}".strip()
                    st.session_state.username = employee_data.get('Email')
                    st.session_state.user_role = employee_data.get('Sub_Department')
                    
                    st.success(f"Welcome back, {st.session_state.full_name}!")
                    st.rerun()
                else:
                    st.error("❌ Invalid email or password. Please try again.")
        else:
            st.warning("⚠️ Please enter both email and password.")

# ========== MAIN APPLICATION LOGIC ==========
# Initialize session state
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

# Check if user is logged in
if not st.session_state.logged_in:
    simple_login_page()
else:
    # User is logged in - show main application
    st.success(f"Welcome, **{st.session_state.full_name}** ({st.session_state.username})")
    
    # Navigation setup
    home_page = st.Page(
        page="home_page.py", 
        title="Home Page",
        icon=":material/home:",
        default=True
    )

    chat_bot = st.Page(
        page="chat_bot.py", 
        title="Get Support",
        icon=":material/support_agent:"
    )

    knowledge_base = st.Page(
        page="knowledgebases.py", 
        title="Knowledge Base",
        icon=":material/cognition:"
    )

    l_hub = st.Page(
        page="leave.py", 
        title="Leave Management",
        icon=":material/flight_takeoff:"
    )

    # ========== NAVIGATION ==========
    page_navigator = st.navigation({
        "Home": [home_page],
        "Help Desk": [chat_bot, knowledge_base],
        "Leave Hub": [l_hub]
    })

    page_navigator.run()

    # Logout button in sidebar
    if st.sidebar.button("🚪 Logout"):
        st.session_state.clear()
        st.success("You have been logged out successfully.")
        st.rerun()
