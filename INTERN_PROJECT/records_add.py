import pandas as pd
import sqlite3

conn = sqlite3.connect(r'leave_management.db')

employee_data = pd.read_csv("data/employee_table.csv")
leave_entry_data = pd.read_csv("data/leave_entries.csv")
leave_entitlements_data = pd.read_csv("data/leave_entitlements_data.csv")

employee_data.to_sql(name="employee_table",con=conn,if_exists='replace',index=False)
leave_entry_data.to_sql(name="leave_entry",con=conn,if_exists='replace',index=False)
leave_entitlements_data.to_sql(name="leave_entitlements_data",con=conn,if_exists='replace',index=False)

