import streamlit as st 
import pandas as pd
import plotly.express as px
from millify import prettify



data = pd.read_csv("partner_streamlit.csv")
st.title("Partner Payroll")

# Dropdown for filtering by partner
selected_partner = st.selectbox(
    "Select Partner:",
    data['Partner'].unique()
)

# Filter data based on selected partner
filtered_df = data[data['Partner'] == selected_partner]

salary = filtered_df['Salary'].sum()
department_avg_sal = round(filtered_df.groupby('Department')['Salary'].mean().reset_index(),0)
headcount = len(filtered_df['EmpID'])
salary = prettify(salary)

col1,col2 = st.columns(2,gap='large')

with col1:
    st.metric('Total Salary Paid',salary,'+0.87%')

with col2:
    st.metric("Current Headcount",headcount,'+1.32%')        
st.subheader('Avg Salary Paid Per Department')
st.dataframe(department_avg_sal,hide_index=True)
    
