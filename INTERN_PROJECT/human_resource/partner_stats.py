import streamlit as st
import pandas as pd
from PIL import Image
import plotly.express as px
import sqlite3
import uuid # Needed for potential record IDs if adding/modifying leaves
from datetime import datetime, timedelta # Needed for date handling

# --- Database connection path for leave management ---
LEAVE_DB_PATH = 'leave_management.db'

def init_leave_db():
    """Initializes the leave_management table if it doesn't exist."""
    conn = sqlite3.connect(LEAVE_DB_PATH)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS leaves (
            id TEXT PRIMARY KEY,
            employee_name TEXT NOT NULL,
            leave_type TEXT NOT NULL,
            start_date TEXT NOT NULL,
            end_date TEXT NOT NULL,
            description TEXT,
            status TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()

@st.cache_data
def get_all_leaves():
    """Fetches all leave records from the leave management database."""
    conn = sqlite3.connect(LEAVE_DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT id, employee_name, leave_type, start_date, end_date, description, status FROM leaves")
    rows = c.fetchall()
    conn.close()
    # Convert sqlite3.Row objects to dictionaries for serializability
    return [dict(row) for row in rows]

# Initialize the leave database when the app starts
init_leave_db()


# --- kenya_towns.py content (as provided) ---
kenya_towns = {
    "Nairobi": [
        "Westlands", "Kilimani", "Kenyatta", "Karen", "Eastleigh",
        "Lang’ata", "South B", "South C", "Ruaraka", "Dagoretti",
        "Kasarani", "Gikambura"
    ],
    "Mombasa": [
        "Mombasa Island", "Nyali", "Likoni", "Changamwe", "Kisauni",
        "Bamburi", "Port Reitz", "Tudor", "Shanzu"
    ],
    "Uasin Gishu (Eldoret)": [
        "Eldoret", "Turbo", "Ziwa", "Moi’s Bridge", "Kesses",
        "Burnt Forest", "Soy"
    ],
    "Kisumu": [
        "Kisumu", "Ahero", "Maseno", "Muhoroni", "Nyahera",
        "Kombewa", "Koru", "Katito", "Kajulu"
    ],
    "Kajiado": [
        "Kajiado", "Ngong", "Kitengela", "Isinya", "Namanga",
        "Ongata Rongai", "Loitokitok", "Ilbisil", "Magadi"
    ]
}


# --- Main HR Portal Content ---
st.title("HR Portal: Leave & Partner Management")

# Load partner data


