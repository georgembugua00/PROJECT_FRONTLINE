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
        conn.row_factory = sqlite3.Row
        return conn
    except sqlite3.Error as e:
        st.error(f"Error connecting to database: {e}")
        return None

# --- Analytics Functions ---

def get_dashboard_metrics():
    """Fetches key metrics for the dashboard."""
    conn = init_db()
    metrics = {
        'pending_count': 0,
        'approved_today': 0,
        'team_on_leave_today': 0,
        'upcoming_leaves': 0,
        'recent_requests': []
    }
    
    if conn:
        try:
            cursor = conn.cursor()
            today = date.today()
            
            # Pending requests count
            cursor.execute("SELECT COUNT(*) as count FROM leave_entries WHERE status = 'Pending'")
            metrics['pending_count'] = cursor.fetchone()['count']
            
            # Approved requests today
            cursor.execute("SELECT COUNT(*) as count FROM leave_entries WHERE status = 'Approved' AND date(start_date) = ?", (today,))
            metrics['approved_today'] = cursor.fetchone()['count']
            
            # Team members currently on leave
            cursor.execute("""
                SELECT COUNT(*) as count FROM leave_entries 
                WHERE status = 'Approved' AND ? BETWEEN start_date AND end_date
            """, (today,))
            metrics['team_on_leave_today'] = cursor.fetchone()['count']
            
            # Upcoming leaves (next 7 days)
            next_week = today + timedelta(days=7)
            cursor.execute("""
                SELECT COUNT(*) as count FROM leave_entries 
                WHERE status = 'Approved' AND start_date BETWEEN ? AND ?
            """, (today, next_week))
            metrics['upcoming_leaves'] = cursor.fetchone()['count']
            
            # Recent requests (last 5)
            cursor.execute("""
                SELECT employee_name, leave_type, start_date, end_date, status
                FROM leave_entries 
                ORDER BY id DESC 
                LIMIT 5
            """)
            metrics['recent_requests'] = [dict(row) for row in cursor.fetchall()]
            
        except sqlite3.Error as e:
            st.error(f"Error fetching metrics: {str(e)}")
        finally:
            conn.close()
    
    return metrics

def get_team_members_on_leave_today():
    """Get list of team members currently on leave."""
    conn = init_db()
    on_leave_today = []
    
    if conn:
        try:
            cursor = conn.cursor()
            today = date.today()
            cursor.execute("""
                SELECT employee_name, leave_type, start_date, end_date
                FROM leave_entries 
                WHERE status = 'Approved' AND ? BETWEEN start_date AND end_date
                ORDER BY employee_name
            """, (today,))
            on_leave_today = [dict(row) for row in cursor.fetchall()]
        except sqlite3.Error as e:
            st.error(f"Error fetching team members on leave: {str(e)}")
        finally:
            conn.close()
    
    return on_leave_today

# --- Import existing functions from the original code ---
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
    """Fetches leave requests based on filters for the team dashboard."""
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

st.set_page_config(layout="wide", page_title="Leave Management - Executive Dashboard")

# --- Custom CSS ---
st.html("""
<style>
    .executive-header {
        background: #F44336 ;
        padding: 2rem;
        border-radius: 15px;
        text-align: center;
        margin-bottom: 2rem;
        box-shadow: 0 10px 25px rgba(0, 0, 0, 0.1);
    }
    .executive-header h1 {
        color: white;
        font-size: 3em; /* Increased by 2pts */
        margin-bottom: 0.5rem;
        font-weight: 300;
    }
    .executive-header p {
        color: rgba(255, 255, 255, 0.9);
        font-size: 1.4em; /* Increased by 2pts */
        margin: 0;
    }
    .metric-card {
        background: white;
        padding: 1.5rem;
        border-radius: 12px;
        text-align: center;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.08);
        border-left: 4px solid #667eea;
        transition: transform 0.2s ease;
    }
    .metric-card:hover {
        transform: translateY(-2px);
    }
    .metric-number {
        font-size: 2.7em; /* Increased by 2pts */
        font-weight: bold;
        color: #ea6680;
        margin: 0.5rem 0;
    }
    .metric-label {
        color: #64748b;
        font-size: 1.1em; /* Increased by 2pts */
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    .quick-action-btn {
        background:yellow;
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.8rem 1.5rem;
        font-size: 1.2rem; /* Increased by 2pts */
        font-weight: 500;
        cursor: pointer;
        transition: all 0.3s ease;
        box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
    }
    .quick-action-btn:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(102, 126, 234, 0.4);
    }
    .section-header {
        color: #374151;
        font-size: 1.7em; /* Increased by 2pts */
        font-weight: 600;
        margin-bottom: 1rem;
        padding-bottom: 0.5rem;
        border-bottom: 2px solid #e5e7eb;
    }
    .alert-pending {
        background-color: #F1C232;
        border-left: 4px solid #f59e0b;
        padding: 1rem;
        border-radius: 8px;
        margin-bottom: 1rem;
    }
    .alert-success {
        background-color: #d1fae5;
        border-left: 4px solid #10b981;
        padding: 1rem;
        border-radius: 8px;
        margin-bottom: 1rem;
    }
    .status-badge {
        padding: 0.25rem 0.75rem;
        border-radius: 20px;
        font-size: 1em; /* Increased by 2pts */
        font-weight: 500;
        text-transform: uppercase;
    }
    .status-pending { background-color: #fef3c7; color: #92400e; }
    .status-approved { background-color: #d1fae5; color: #065f46; }
    .status-declined { background-color: #fee2e2; color: #991b1b; }
</style>
""")

# --- Executive Header ---
st.html("""
<div class="executive-header">
    <h1>Executive Dashboard</h1>
    <p>Leave Management Overview & Quick Actions</p>
</div>
""")

# --- Dashboard Metrics ---
metrics = get_dashboard_metrics()

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.html(f"""
    <div class="metric-card">
        <div class="metric-number">{metrics['pending_count']}</div>
        <div class="metric-label">Pending Requests</div>
    </div>
    """)

with col2:
    st.html(f"""
    <div class="metric-card">
        <div class="metric-number">{metrics['team_on_leave_today']}</div>
        <div class="metric-label">Team on Leave Today</div>
    </div>
    """)

with col3:
    st.html(f"""
    <div class="metric-card">
        <div class="metric-number">{metrics['upcoming_leaves']}</div>
        <div class="metric-label">Upcoming Leaves (7 days)</div>
    </div>
    """)

with col4:
    st.html(f"""
    <div class="metric-card">
        <div class="metric-number">{metrics['approved_today']}</div>
        <div class="metric-label">Approved Today</div>
    </div>
    """)

st.markdown("<br>", unsafe_allow_html=True)

# --- Quick Actions & Alerts ---
col1, col2 = st.columns([2, 1])

with col1:
    if metrics['pending_count'] > 0:
        st.html(f"""
        <div class="alert-pending">
            <strong>⚠️ Action Required:</strong> You have {metrics['pending_count']} pending leave request(s) awaiting your review.
        </div>
        """)
    else:
        st.html("""
        <div class="alert-success">
            <strong>✅ All Clear:</strong> No pending leave requests at this time.
        </div>
        """)

with col2:
    if st.button("🔍 Review Pending Requests", key="quick_pending", help="Go to pending requests tab"):
        st.switch_page("leave_centre.py")

# --- Team Status Today ---
st.markdown("### 👥 Team Status Today")
st.divider()

team_on_leave = get_team_members_on_leave_today()

if team_on_leave:
    for member in team_on_leave:
        col1, col2, col3 = st.columns([2, 1, 2])
        with col1:
            st.write(f"**{member['employee_name']}**")
        with col2:
            st.html(f'<span class="status-badge status-approved">{member["leave_type"]}</span>')
        with col3:
            st.write(f"Until {member['end_date']}")
else:
    st.info("✨ Full team available today!")

st.markdown("<br>", unsafe_allow_html=True)

# --- Recent Activity ---
st.markdown("### 📋 Recent Leave Activity")
st.divider()


if metrics['recent_requests']:
    for i, request in enumerate(metrics['recent_requests'][:3]):  # Show only top 3
        with st.container():
            col1, col2, col3, col4 = st.columns([2, 1, 2, 1])
            with col1:
                st.write(f"**{request['employee_name']}**")
            with col2:
                st.write(request['leave_type'])
            with col3:
                st.write(f"{request['start_date']} to {request['end_date']}")
            with col4:
                status_class = f"status-{request['status'].lower()}"
                st.html(f'<span class="status-badge {status_class}">{request["status"]}</span>')
        
        if i < len(metrics['recent_requests']) - 1:
            st.markdown("---")
else:
    st.info("No recent leave activity.")

# --- Navigation Tabs ---
st.divider()


# --- Footer ---
st.markdown("---")
st.html("""
<div style="text-align: center; color: #6b7280; padding: 1rem;">
    <p>Leave Management System | Executive Dashboard | Built with Streamlit & SQLite</p>
</div>
""")