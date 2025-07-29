import streamlit as st   
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from millify import prettify
import sqlite3
from datetime import datetime

# Database connection function
@st.cache_data
def get_data_from_db():
    """Fetch all data from SQLite database"""
    try:
        # Connect to SQLite database
        conn = sqlite3.connect("leave_management.db")  # Update with your actual database name
        
        # Fetch employee/partner data
        employee_query = """
        SELECT * FROM employee_table 
        -- Add any joins if needed for partner information
        """
        data = pd.read_sql_query(employee_query, conn)
        
        # Fetch leave data
        leave_query = """
        SELECT 
            l.*,
            e.First_Name as employee_name,
            e.Partner_Name,
            e.Department
        FROM leave_entries l
        LEFT JOIN employee_table_rows e ON l.leave_id = e.id
        ORDER BY l.id DESC
        """
        leave_data = pd.read_sql_query(leave_query, conn)
        
        conn.close()
        return data, leave_data
        
    except Exception as e:
        st.error(f"Database connection error: {e}")
        return pd.DataFrame(), pd.DataFrame()

# Load data from database
data, leave_data = get_data_from_db()

# Check if data is loaded successfully
if data.empty:
    st.error("No employee data found in database. Please check your database connection and table structure.")
    st.stop()

st.title("Frontline Agent Program")

# Partner filter for dynamic metrics
if 'Partner' in data.columns:
    partner_column = 'Partner'
elif 'partner' in data.columns:
    partner_column = 'partner'
else:
    st.error("Partner column not found in database. Please check your table structure.")
    st.stop()

selected_partners = st.multiselect(
    "Select Partners to Monitor:",
    options=data[partner_column].unique(),
    default=data[partner_column].unique()  # Default to all partners
)

# Filter data based on selected partners
filtered_data = data[data[partner_column].isin(selected_partners)] if selected_partners else data

st.divider()

# Dynamic Key Metrics Row
col1, col2, col3, col4 = st.columns(4)

# Calculate dynamic metrics
total_employees = len(filtered_data)

# Handle different possible column names for termination date
termination_columns = ['DateofTermination', 'date_of_termination', 'termination_date', 'end_date']
termination_col = None
for col in termination_columns:
    if col in filtered_data.columns:
        termination_col = col
        break

if termination_col:
    terminated_employees = filtered_data[termination_col].notnull().sum()
else:
    terminated_employees = 0
    st.warning("Termination date column not found in database")

active_employees = total_employees - terminated_employees

# Calculate leave liability dynamically
liability_columns = ['leave_entitlements', 'Leave_Liability', 'leave_liability']
total_leave_liability = 0
for col in liability_columns:
    if col in filtered_data.columns:
        total_leave_liability = filtered_data[col].sum()
        break

# Calculate turnover rate
turnover_rate = (terminated_employees / total_employees * 100) if total_employees > 0 else 0

# Calculate average leave days per employee
leave_day_columns = ['Cumulative_Leave_Days', 'cumulative_leave_days', 'total_leave_days']
avg_leave_days = 0
for col in leave_day_columns:
    if col in filtered_data.columns:
        avg_leave_days = filtered_data[col].mean() if total_employees > 0 else 0
        break

with col1:
    st.metric(
        label="👥 Total Employees",
        value=total_employees,
        delta=f"{len(selected_partners)} partners monitored"
    )

with col2:
    st.metric(
        label="✅ Active Employees", 
        value=active_employees,
        delta=f"{active_employees/total_employees*100:.1f}%" if total_employees > 0 else "0%"
    )

with col3:
    st.metric(
        label="⚠️ Terminated Employees",
        value=terminated_employees,
        delta=f"{terminated_employees/total_employees*100:.1f}%" if total_employees > 0 else "0%"
    )

with col4:
    st.metric(
        label="📈 Turnover Rate",
        value=f"{turnover_rate:.1f}%",
        delta="Good" if turnover_rate <= 15 else "High Turnover",
        delta_color="normal" if turnover_rate <= 15 else "inverse"
    )

st.divider()

# Partner-specific metrics with dynamic calculations
with st.container(border=False):
    col1, col2 = st.columns(2, gap='medium', vertical_alignment='top')
    
    # Sheer Logic Metrics
    sheerlogic_data = filtered_data[filtered_data[partner_column] == 'Sheer Logic']
    sheerlogic_employees = len(sheerlogic_data)
    sheerlogic_terminated = sheerlogic_data[termination_col].notnull().sum() if termination_col else 0
    
    # Dynamic leave liability calculation for Sheer Logic
    sheerlogic_liability = 0
    for col in liability_columns:
        if col in sheerlogic_data.columns:
            sheerlogic_liability = sheerlogic_data[col].sum()
            break
    
    # Calculate month-over-month change (you'd need historical data for real delta)
    sheerlogic_liability_change = 2.5  # Placeholder - calculate from historical data
    
    with col1:
        if len(sheerlogic_data) > 0:
            st.image('file (1).svg', width=360)
            col3, col4 = st.columns(2)
            with col3:
                st.metric(
                    'Current Leave Liability in KES',
                    prettify(round(sheerlogic_liability)),
                    f'+{sheerlogic_liability_change}%' if sheerlogic_liability_change > 0 else f'{sheerlogic_liability_change}%'
                )
            with col4:    
                st.metric(
                    'Current Headcount',
                    sheerlogic_employees,
                    f'Active: {sheerlogic_employees - sheerlogic_terminated}'
                )
        else:
            st.info("No Sheer Logic employees found in selected data")

    # Fine Media Metrics  
    fine_media_data = filtered_data[filtered_data[partner_column] == 'Fine Media']
    fine_media_employees = len(fine_media_data)
    fine_media_terminated = fine_media_data[termination_col].notnull().sum() if termination_col else 0
    
    # Dynamic leave liability calculation for Fine Media
    fine_media_liability = 0
    for col in liability_columns:
        if col in fine_media_data.columns:
            fine_media_liability = fine_media_data[col].sum()
            break
    
    fine_media_liability_change = -2.5  # Placeholder - calculate from historical data
    
    with col2:
        if len(fine_media_data) > 0:
            st.image("file.svg", width=450) 
            col5, col6 = st.columns(2)
            with col5:
                st.metric(
                    'Current Leave Liability in KES',
                    prettify(round(fine_media_liability)),
                    f'+{fine_media_liability_change}%' if fine_media_liability_change > 0 else f'{fine_media_liability_change}%'
                )
            with col6:    
                st.metric(
                    'Current Headcount',
                    fine_media_employees,
                    f'Active: {fine_media_employees - fine_media_terminated}'
                )
        else:
            st.info("No Fine Media employees found in selected data")

st.divider()

# Additional Dynamic Metrics
col1, col2, col3 = st.columns(3)

with col1:
    performance_columns = ['PerformanceScore', 'performance_score', 'performance_rating']
    avg_performance = 0
    for col in performance_columns:
        if col in filtered_data.columns:
            avg_performance = filtered_data[col].mean()
            break
    
    st.metric(
        label="📊 Avg Performance Score",
        value=f"{avg_performance:.1f}",
        delta="Above Target" if avg_performance >= 3.5 else "Below Target",
        delta_color="normal" if avg_performance >= 3.5 else "inverse"
    )

with col2:
    denied_leave_columns = ['Amnt_Denied_Leave_Request', 'denied_leave_requests', 'leave_denials']
    total_leave_requests = 0
    for col in denied_leave_columns:
        if col in filtered_data.columns:
            total_leave_requests = filtered_data[col].sum()
            break
    
    st.metric(
        label="📋 Leave Requests Denied",
        value=int(total_leave_requests),
        delta=f"Denial rate: {(total_leave_requests/total_employees*100):.1f}%" if total_employees > 0 else "0%"
    )

with col3:
    total_leave_liability_formatted = prettify(round(total_leave_liability))
    st.metric(
        label="💰 Total Leave Liability",
        value=f"KES {total_leave_liability_formatted}",
        delta=f"Per employee: KES {prettify(round(total_leave_liability/total_employees))}" if total_employees > 0 else "KES 0"
    )

# Pie Chart with filtered data
leave_days_col = None
for col in leave_day_columns:
    if col in filtered_data.columns:
        leave_days_col = col
        break

if leave_days_col:
    fig = px.pie(
        data_frame=filtered_data,
        names=partner_column,
        values=leave_days_col,
        title="Cumulative Leave Days by Partner"
    )    
    st.plotly_chart(fig)

st.divider()

# Performance Analysis with Dynamic Filtering
try:
    st.subheader("Partner Performance Analysis")

    # Dropdown for filtering by partner
    selected_partner = st.selectbox(
        "Select Partner for Detailed Analysis:",
        filtered_data[partner_column].unique() if len(filtered_data) > 0 else ['No data available']
    )

    if len(filtered_data) > 0 and selected_partner in filtered_data[partner_column].values:
        # Filter data based on selected partner
        partner_filtered_df = filtered_data[filtered_data[partner_column] == selected_partner]

        # Dynamic performance metrics
        performance_col = None
        for col in performance_columns:
            if col in partner_filtered_df.columns:
                performance_col = col
                break
        
        if performance_col:
            performance_counts = partner_filtered_df[performance_col].value_counts().reset_index()
            performance_counts.columns = [performance_col, 'count']
            
            # Create performance chart
            perform_graph = px.bar(
                data_frame=performance_counts,
                x=performance_col,
                y='count',
                title=f"Performance Distribution - {selected_partner}"
            )
            
            st.plotly_chart(perform_graph)
            
            # Additional partner-specific metrics
            col1, col2, col3 = st.columns(3)
            
            with col1:
                high_performers = len(partner_filtered_df[partner_filtered_df[performance_col] >= 4])
                st.metric(
                    "🌟 High Performers (4+)",
                    high_performers,
                    f"{high_performers/len(partner_filtered_df)*100:.1f}%" if len(partner_filtered_df) > 0 else "0%"
                )
            
            with col2:
                low_performers = len(partner_filtered_df[partner_filtered_df[performance_col] <= 2])
                st.metric(
                    "⚠️ Low Performers (≤2)",
                    low_performers,
                    f"{low_performers/len(partner_filtered_df)*100:.1f}%" if len(partner_filtered_df) > 0 else "0%"
                )
                
            with col3:
                partner_turnover = partner_filtered_df[termination_col].notnull().sum() if termination_col else 0
                partner_turnover_rate = (partner_turnover / len(partner_filtered_df) * 100) if len(partner_filtered_df) > 0 else 0
                st.metric(
                    "📉 Partner Turnover Rate",
                    f"{partner_turnover_rate:.1f}%",
                    "Healthy" if partner_turnover_rate <= 10 else "Concerning",
                    delta_color="normal" if partner_turnover_rate <= 10 else "inverse"
                )

except Exception as e:
    st.error(f"An error occurred while loading partner data: {e}")



# Database connection info
st.sidebar.markdown("### Database Connection")
st.sidebar.info(f"Connected to SQLite database\nEmployee records: {len(data)}\nLeave records: {len(leave_data)}")

# Refresh data button
if st.sidebar.button("🔄 Refresh Data"):
    st.cache_data.clear()
    st.rerun()
