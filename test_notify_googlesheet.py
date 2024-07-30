import ezsheets
import datetime

# Function to generate a sheet name based on the current date and time
def generate_sheet_name():
    now = datetime.datetime.now()
    date_str = now.strftime('%d_%m_%Y')
    
    if now.time() >= datetime.time(0, 0, 0) and now.time() <= datetime.time(11, 59, 59):
        time_str = 'Enter_work1'
    elif now.time() >= datetime.time(12, 0, 0) and now.time() <= datetime.time(23, 59, 59):
        time_str = 'Leave_work'
    else:
        time_str = 'Other_time'

    return f"{date_str}_{time_str}"

# Open the spreadsheet
s = ezsheets.Spreadsheet('https://docs.google.com/spreadsheets/d/1MNhHL8TpBuiTR5VS1YPEzdyvadxEB5F_iKs4TVUkBZo/edit?gid=1143167581#gid=1143167581')

# Generate a new sheet title based on the current date and time
new_sheet_title = generate_sheet_name()
new_sheet = s.createSheet(title=new_sheet_title)

# Get the newly created sheet
sh = s.sheets[-1]

print(f"Created and using new sheet with title: {sh.title}")
