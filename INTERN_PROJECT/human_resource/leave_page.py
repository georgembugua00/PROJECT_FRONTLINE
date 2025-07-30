import streamlit as st
import pandas as pd
import sqlite3
from datetime import date, datetime

# Define the path to your SQLite database
DB_PATH = 'leave_management.db'

def init_db():
    """
    Initializes the SQLite database and creates the 'leaves' table if it doesn't exist.
    This function should be called once at the start of your main application.
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('''
            CREATE TABLE IF NOT EXISTS leave_entries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                employee_name TEXT NOT NULL,
                leave_type TEXT NOT NULL,
                start_date TEXT NOT NULL, -- Changed to TEXT for ISO format
                end_date TEXT NOT NULL,   -- Changed to TEXT for ISO format
                description TEXT,
                attachment BOOLEAN,
                status TEXT NOT NULL,
                decline_reason TEXT,
                recall_reason TEXT
            )
        ''')
        conn.commit()
        conn.close()
        # print(f"Database initialized at {DB_PATH}") # Comment out for cleaner Streamlit output
    except sqlite3.Error as e:
        st.error(f"Error initializing database: {e}") # Use st.error for Streamlit

def apply_for_leave(employee_name, leave_type, start_date, end_date, description, attachment):
    """
    Adds a new leave application to the database with 'Pending' status.
    Dates are converted to ISO format strings for storage.
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('''
            INSERT INTO leave_entries (employee_name, leave_type, start_date, end_date, description, attachment, status)
            VALUES (?, ?, ?, ?, ?, ?, 'Pending')
        ''', (employee_name, leave_type, start_date.isoformat(), end_date.isoformat(), description, attachment))
        conn.commit()
        conn.close()
        st.success(f"Leave application submitted for {employee_name}") # Use st.success for Streamlit
    except sqlite3.Error as e:
        st.error(f"Error applying for leave: {e}") # Use st.error for Streamlit

def get_leave_history(employee_name):
    """
    Fetches the leave history for a specific employee.
    Returns a list of dictionaries with column names.
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row # Enable dictionary-like access
        c = conn.cursor()
        c.execute("SELECT leave_type, start_date, end_date, description, status FROM leave_entries WHERE employee_name = ?", (employee_name,))
        history = [dict(row) for row in c.fetchall()]
        conn.close()
        return history
    except sqlite3.Error as e:
        st.error(f"Error fetching leave history: {e}")
        return []

def get_all_pending_leaves():
    """
    Fetches all leave requests with a 'Pending' status for the manager's review.
    Returns a list of dictionaries.
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute("SELECT id, employee_name, leave_type, start_date, end_date, description FROM leave_entries WHERE status = 'Pending'")
        pending_leaves = [dict(row) for row in c.fetchall()]
        conn.close()
        return pending_leaves
    except sqlite3.Error as e:
        st.error(f"Error fetching pending leaves: {e}")
        return []

def update_leave_status(leave_id, new_status, reason=None):
    """
    Updates the status of a leave request (Approved, Declined, Recalled, Withdrawn).
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        if new_status == "Declined":
            c.execute("UPDATE leave_entries SET status = ?, decline_reason = ?, recall_reason = '' WHERE id = ?", (new_status, reason, leave_id))
        elif new_status == "Recalled":
            c.execute("UPDATE leave_entries SET status = ?, recall_reason = ?, decline_reason = '' WHERE id = ?", (new_status, reason, leave_id))
        elif new_status == "Withdrawn":
            c.execute("UPDATE leave_entries SET status = ?, recall_reason = ?, decline_reason = '' WHERE id = ?", (new_status, reason, leave_id))
        else: # Approved
            c.execute("UPDATE leave_entries SET status = ?, decline_reason = '', recall_reason = '' WHERE id = ?", (new_status, leave_id))
        conn.commit()
        conn.close()
        st.success(f"Leave ID {leave_id} status updated to {new_status}")
    except sqlite3.Error as e:
        st.error(f"Error updating leave status: {e}")

def get_team_leaves(status_filter=None, leave_type_filter=None, employee_filter=None):
    """
    Fetches all team leaves with optional filters for the manager's dashboard.
    Returns a list of dictionaries.
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        
        query = "SELECT employee_name, leave_type, start_date, end_date, status, description, decline_reason, recall_reason FROM leave_entries WHERE 1=1"
        params = []

        if status_filter:
            placeholders = ','.join('?' for _ in status_filter)
            query += f" AND status IN ({placeholders})"
            params.extend(status_filter)
            
        if leave_type_filter:
            placeholders = ','.join('?' for _ in leave_type_filter)
            query += f" AND leave_type IN ({placeholders})"
            params.extend(leave_type_filter)

        if employee_filter and employee_filter != "All Team Members":
            query += " AND employee_name = ?"
            params.append(employee_filter)

        c.execute(query, params)
        leaves = [dict(row) for row in c.fetchall()]
        conn.close()
        return leaves
    except sqlite3.Error as e:
        st.error(f"Error fetching team leaves: {e}")
        return []

def get_all_employees():
    """
    Gets a unique list of all employees who have applied for leave.
    Returns a list of employee names.
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT DISTINCT employee_name FROM leave_entries")
        employees = [row[0] for row in c.fetchall()]
        conn.close()
        return employees
    except sqlite3.Error as e:
        st.error(f"Error fetching all employees: {e}")
        return []

def get_all_leaves():
    """
    Fetches all leave records from the database.
    Returns a list of dictionaries, each representing a leave record.
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute("SELECT id, employee_name, leave_type, start_date, end_date, description, status FROM leave_entries")
        rows = c.fetchall()
        conn.close()
        
        leaves = []
        for row in rows:
            leaves.append(dict(row))
        return leaves
    except sqlite3.Error as e:
        st.error(f"Error fetching all leaves: {e}")
        return []

def withdraw_leave(leave_id, recall_reason=None):
    """
    Marks a leave request as 'Withdrawn' with an optional reason.
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("UPDATE leave_entries SET status = 'Withdrawn', recall_reason = ?, decline_reason = '' WHERE id = ?", (recall_reason, leave_id))
        conn.commit()
        conn.close()
        st.info(f"Leave ID {leave_id} withdrawn.")
    except sqlite3.Error as e:
        st.error(f"Error withdrawing leave: {e}")

# --- New functions for HR Dashboard (leave_page.py) - Modified for dynamic metrics ---

def calculate_leave_days(start_date_str, end_date_str):
    """Calculates the number of days between start and end dates (inclusive)."""
    try:
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
        return (end_date - start_date).days + 1
    except ValueError:
        return 0 # Handle potential bad date formats

def get_approved_days_for_partner_by_year(partner_name, year):
    """
    Calculates total approved leave days for a specific partner in a given year.
    Assumes 'employee_name' can be used to group by 'partner'.
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        # Query for dates within the specified year
        c.execute(f"""
            SELECT start_date, end_date
            FROM leave_entries
            WHERE status = 'Approved'
            AND employee_name LIKE ?
            AND SUBSTR(start_date, 1, 4) = ?
        """, (f"%{partner_name}%", str(year)))
        rows = c.fetchall()
        conn.close()
        
        total_days = 0
        for row in rows:
            total_days += calculate_leave_days(row[0], row[1])
        return total_days
    except sqlite3.Error as e:
        st.error(f"Error getting approved days for partner {partner_name} in {year}: {e}")
        return 0

def get_denied_requests_for_partner_by_year(partner_name, year):
    """
    Counts total denied leave requests for a specific partner in a given year.
    Assumes 'employee_name' can be used to group by 'partner'.
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute(f"""
            SELECT COUNT(id)
            FROM leave_entries
            WHERE status = 'Declined'
            AND employee_name LIKE ?
            AND SUBSTR(start_date, 1, 4) = ?
        """, (f"%{partner_name}%", str(year)))
        denied_requests = c.fetchone()[0]
        conn.close()
        return denied_requests if denied_requests is not None else 0
    except sqlite3.Error as e:
        st.error(f"Error getting denied requests for partner {partner_name} in {year}: {e}")
        return 0

def get_cumulated_leave_days_for_partner_by_year(partner_name, year):
    """
    Calculates total cumulated leave days for a specific partner in a given year.
    This sums up the duration of all non-denied/non-withdrawn leaves that started in the year.
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute(f"""
            SELECT start_date, end_date
            FROM leave_entries
            WHERE status IN ('Approved', 'Pending')
            AND employee_name LIKE ?
            AND SUBSTR(start_date, 1, 4) = ?
        """, (f"%{partner_name}%", str(year)))
        rows = c.fetchall()
        conn.close()

        total_cumulated_days = 0
        for row in rows:
            total_cumulated_days += calculate_leave_days(row[0], row[1])
        return total_cumulated_days if total_cumulated_days is not None else 0
    except sqlite3.Error as e:
        st.error(f"Error getting cumulated leave days for partner {partner_name} in {year}: {e}")
        return 0


def get_upcoming_leaves():
    """
    Fetches leave requests that are approved and start in the future.
    Returns a list of dictionaries.
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        today = date.today().isoformat()
        c.execute("""
            SELECT employee_name, leave_type, start_date, end_date
            FROM leave_entries
            WHERE status = 'Approved' AND start_date > ?
            ORDER BY start_date ASC
        """, (today,))
        rows = c.fetchall()
        conn.close()
        
        upcoming_leaves = [dict(row) for row in rows]
        return upcoming_leaves
    except sqlite3.Error as e:
        st.error(f"Error fetching upcoming leaves: {e}")
        return []

def get_current_leaves():
    """
    Fetches leave requests that are currently active (start_date <= today <= end_date).
    Returns a list of dictionaries.
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        today = date.today().isoformat()
        c.execute("""
            SELECT employee_name, leave_type, start_date, end_date
            FROM leave_entries
            WHERE status = 'Approved' AND start_date <= ? AND end_date >= ?
            ORDER BY start_date ASC
        """, (today, today))
        rows = c.fetchall()
        conn.close()
        
        current_leaves = [dict(row) for row in rows]
        return current_leaves
    except sqlite3.Error as e:
        st.error(f"Error fetching current leaves: {e}")
        return []

# Initialize DB (ensure this runs only once per session)
if 'db_initialized' not in st.session_state:
    init_db()
    st.session_state['db_initialized'] = True


### Streamlit App Layout (`leave_management_page` function)

def leave_management_page():
    st.title("📅 Leave Management Dashboard (HR View)")

    # --- Configuration for Dynamic Metrics ---
    current_year = date.today().year
    previous_year = current_year - 1

    # --- Fetching data for Fine Media ---
    approved_days_finemedia_current = get_approved_days_for_partner_by_year("Fine Media", current_year)
    denied_requests_finemedia_current = get_denied_requests_for_partner_by_year("Fine Media", current_year)
    cumulated_leave_finemedia_current = get_cumulated_leave_days_for_partner_by_year("Fine Media", current_year)

    approved_days_finemedia_prev = get_approved_days_for_partner_by_year("Fine Media", previous_year)
    denied_requests_finemedia_prev = get_denied_requests_for_partner_by_year("Fine Media", previous_year)
    cumulated_leave_finemedia_prev = get_cumulated_leave_days_for_partner_by_year("Fine Media", previous_year)

    # --- Fetching data for Sheer Logic ---
    approved_days_sheerlogic_current = get_approved_days_for_partner_by_year("Sheer Logic", current_year)
    denied_requests_sheerlogic_current = get_denied_requests_for_partner_by_year("Sheer Logic", current_year)
    cumulated_leave_sheerlogic_current = get_cumulated_leave_days_for_partner_by_year("Sheer Logic", current_year)

    approved_days_sheerlogic_prev = get_approved_days_for_partner_by_year("Sheer Logic", previous_year)
    denied_requests_sheerlogic_prev = get_denied_requests_for_partner_by_year("Sheer Logic", previous_year)
    cumulated_leave_sheerlogic_prev = get_cumulated_leave_days_for_partner_by_year("Sheer Logic", previous_year)

    # --- Calculate Deltas ---
    def calculate_delta(current_value, previous_value):
        if previous_value == 0:
            return None # Avoid division by zero, or handle as appropriate (e.g., "New data")
        delta = ((current_value - previous_value) / previous_value) * 100
        return f"{delta:.1f}%"

    delta_approved_finemedia = calculate_delta(approved_days_finemedia_current, approved_days_finemedia_prev)
    delta_denied_finemedia = calculate_delta(denied_requests_finemedia_current, denied_requests_finemedia_prev)
    delta_cumulated_finemedia = calculate_delta(cumulated_leave_finemedia_current, cumulated_leave_finemedia_prev)

    delta_approved_sheerlogic = calculate_delta(approved_days_sheerlogic_current, approved_days_sheerlogic_prev)
    delta_denied_sheerlogic = calculate_delta(denied_requests_sheerlogic_current, denied_requests_sheerlogic_prev)
    delta_cumulated_sheerlogic = calculate_delta(cumulated_leave_sheerlogic_current, cumulated_leave_sheerlogic_prev)

    # Fetch Upcoming and Currently on Leave from DB
    upcoming_leaves_df = pd.DataFrame(get_upcoming_leaves())
    current_leaves_df = pd.DataFrame(get_current_leaves())

    fine_media_col, sheerlogic_col = st.columns(2)
    
    with fine_media_col:
        # st.image("/Users/danielwanganga/Documents/Channel Partner/saidii_multi_page/inhouse/images/file.svg",width=120)
        st.subheader("Fine Media Metrics")
        tab1, tab2, tab3 = st.tabs(['Approved','Declined','Cumulated'])
        with tab1:
            st.metric("Days Approved", approved_days_finemedia_current, delta=delta_approved_finemedia)
        with tab2:
            st.metric("Declined Leave Requests", denied_requests_finemedia_current, delta=delta_denied_finemedia)
        with tab3:
            st.metric("Total Cumulated Leave Days", cumulated_leave_finemedia_current, delta=delta_cumulated_finemedia)        


    with sheerlogic_col:
        # st.image('/Users/danielwanganga/Documents/Channel Partner/saidii_multi_page/inhouse/images/file (1).svg',width=100)
        st.subheader("Sheer Logic Metrics")
        tab1, tab2, tab3 = st.tabs(['Approved','Declined','Cumulated'])
        with tab1:  
            st.metric("Days Approved", approved_days_sheerlogic_current, delta=delta_approved_sheerlogic)
        with tab2:
            st.metric("Declined Leave Requests", denied_requests_sheerlogic_current, delta=delta_denied_sheerlogic)
        with tab3:
            st.metric("Total Cumulated Leave Days", cumulated_leave_sheerlogic_current, delta=delta_cumulated_sheerlogic) 
                
    st.markdown("---")
    st.subheader("Upcoming Leaves")
    if not upcoming_leaves_df.empty:
        st.dataframe(data=upcoming_leaves_df)
    else:
        st.info("No upcoming leaves found.")

    st.subheader("Currently on Leave")
    if not current_leaves_df.empty:
        st.dataframe(data=current_leaves_df)
    else:
        st.info("No employees are currently on leave.")

# Call the main page function
leave_management_page()
