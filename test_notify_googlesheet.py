"""
#gen sheet : YyYyMmDd in realtime

import ezsheets
import datetime

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

s = ezsheets.Spreadsheet('1MNhHL8TpBuiTR5VS1YPEzdyvadxEB5F_iKs4TVUkBZo')

new_sheet_title = generate_sheet_name()
new_sheet = s.createSheet(title=new_sheet_title)

sh = s.sheets[-1]

print(f"Created and using new sheet with title: {sh.title}")
"""

"""------------------------------------------------------------------------------------------------------------------------------------"""


"""
#gen Spreadsheet : YyYyMmDd in realtime

import ezsheets
from datetime import datetime

now = datetime.now()

date_str = now.strftime("%Y-%m-%d")

import datetime

if now.time() >= datetime.time(0, 0, 0) and now.time() <= datetime.time(11, 59, 59):
    time_based_name = 'Enter_work'
elif now.time() >= datetime.time(12, 0, 0) and now.time() <= datetime.time(23, 59, 59):
    time_based_name = 'Leave_work'
else:
    time_based_name = 'Other_work'

spreadsheet_name = f"{date_str}_{time_based_name}"

new_spreadsheet = ezsheets.createSpreadsheet(spreadsheet_name)

print('New spreadsheet created:')
print('Spreadsheet ID:', new_spreadsheet.spreadsheetId)

s = ezsheets.Spreadsheet(new_spreadsheet.spreadsheetId)

sh = s[0]
"""