import streamlit as st
import pandas as pd
from datetime import datetime
import os
import win32com.client as win32

# --------------- Configuration ---------------

VENDORS = [
    {"vendor": "VendorA", "vendor_code": "V001"},
    {"vendor": "VendorB", "vendor_code": "V002"},
    {"vendor": "VendorC", "vendor_code": "V003"}
]

USED_SERIALS_FILE = "used_serials.csv"

# --------------- Helper Functions ---------------

def load_used_serials():
    if os.path.exists(USED_SERIALS_FILE):
        return pd.read_csv(USED_SERIALS_FILE)
    else:
        return pd.DataFrame(columns=["imsi", "ser_nb"])

def save_used_serials(df):
    df.to_csv(USED_SERIALS_FILE, index=False)

def generate_sim_files(batch_no, profile, quantity, start_imsi, start_serial, no_of_files):
    imsi = int(start_imsi)
    serial = int(start_serial)
    sims_per_file = quantity // no_of_files
    remainder = quantity % no_of_files
    today_str = datetime.today().strftime('%Y-%m-%d')

    used_serials = load_used_serials()
    existing_imsi = set(used_serials["imsi"].astype(str))
    existing_serials = set(used_serials["ser_nb"].astype(str))

    control_data = []
    new_serials = []

    vendor_index = 0
    vendor_count = len(VENDORS)

    for file_no in range(1, no_of_files + 1):
        file_quantity = sims_per_file + (1 if file_no <= remainder else 0)
        file_name = f"SIM_File_{file_no}.xlsx"
        file_data = []

        for _ in range(file_quantity):
            while str(imsi) in existing_imsi or str(serial) in existing_serials:
                imsi += 1
                serial += 1

            vendor = VENDORS[vendor_index % vendor_count]
            vendor_index += 1

            row = {
                'file': file_name,
                'utilizations': '',
                'date range': f"{today_str} - {today_str}",
                'customer': 'Default Customer',
                'quantity': 1,
                'type': 'SIM',
                'profile': profile,
                'elect': '',
                'graph_ref': '',
                'batch': batch_no,
                'start_imsi': str(imsi),
                'ser_nb': str(serial),
                'vendor': vendor["vendor"],
                'vendor_code': vendor["vendor_code"],
                'var_out': ''
            }
            file_data.append(row)
            control_data.append([file_no, batch_no, profile, 1, imsi, serial])
            new_serials.append({"imsi": imsi, "ser_nb": serial})
            imsi += 1
            serial += 1

        df = pd.DataFrame(file_data)
        df.to_excel(file_name, index=False)

    control_df = pd.DataFrame(control_data, columns=['file_no', 'batch_no', 'profile', 'quantity', 'imsi', 'ser_nb'])
    control_df.to_excel("control_file.xlsx", index=False)

    updated_serials_df = pd.concat([used_serials, pd.DataFrame(new_serials)], ignore_index=True)
    save_used_serials(updated_serials_df)

    return quantity

def draft_outlook_email(batch_no, quantity, recipients, cc_list=None):
    outlook = win32.Dispatch('Outlook.Application')
    mail = outlook.CreateItem(0)

    mail.Subject = f"SIM Batch {batch_no} - {quantity} SIMs Generated"
    mail.To = "; ".join(recipients)
    if cc_list:
        mail.CC = "; ".join(cc_list)

    mail.Body = f"""
Dear Team,

Please find attached the generated SIM files and the control file for:

    Batch Number : {batch_no}
    Quantity      : {quantity}
    Profile       : STANDARD

Ensure the files are reviewed and uploaded accordingly.

Regards,
SIM Automation Bot
    """

    control_file = "control_file.xlsx"
    if os.path.exists(control_file):
        mail.Attachments.Add(os.path.abspath(control_file))

    for i in range(1, 20):
        sim_file = f"SIM_File_{i}.xlsx"
        if os.path.exists(sim_file):
            mail.Attachments.Add(os.path.abspath(sim_file))

    mail.Display()

# --------------- Streamlit Interface ---------------

st.title("📶 SIM Serial Generator with Outlook Automation")

with st.form("sim_form"):
    batch_no = st.text_input("Batch Number", value="BATCH20250729")
    profile = st.selectbox("Profile", ["STANDARD", "SPECIAL"])
    quantity = st.number_input("Quantity", min_value=1, value=100)
    start_imsi = st.text_input("Start IMSI", value="639020100000001")
    start_serial = st.text_input("Start Serial No", value="100000000001")
    no_of_files = st.number_input("Number of Files", min_value=1, value=3)
    recipients = st.text_area("To (semicolon-separated emails)", value="your_email@example.com").split(";")
    cc = st.text_area("CC (optional, semicolon-separated)", value="").split(";")

    submitted = st.form_submit_button("Generate SIM Files & Draft Email")

if submitted:
    with st.spinner("Generating SIM files..."):
        generated_qty = generate_sim_files(batch_no, profile, quantity, start_imsi, start_serial, no_of_files)
    st.success(f"{generated_qty} SIM records generated in {no_of_files} file(s).")

    with st.spinner("Creating Outlook email draft..."):
        draft_outlook_email(batch_no, quantity, recipients, cc)
    st.success("Outlook email drafted with all files attached.")
