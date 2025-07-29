# --- main.py ---
import streamlit as st
#from inhouse.leave_page import leave_management_page
#from inhouse.partner_stats import hr_portal_page

st.set_page_config(page_title="HR & Leave App", layout="wide")



home = st.Page(
    title="Home",
    page='home.py',   
    default=True
)
   

leave_management = st.Page(
    title="Partner Stats",
    page='leave_page.py',   
)

performance = st.Page(
    title='Agent Hub',
    page='partner_stats.py'
)
payroll = st.Page(
    title='Payroll',
    page='payroll.py'
)


navigation = st.navigation({
    "Home": [home],
    'Leave Hub' :[leave_management],
    "Payroll" : [payroll],
})

navigation.run()


