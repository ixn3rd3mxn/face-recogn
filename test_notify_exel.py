import gspread
from google.oauth2.service_account import Credentials

scopes = ["https://www.googleapis.com/auth/spreadsheets"]
creds = Credentials.from_service_account_file("credentials.json", scopes=scopes)
client = gspread.authorize(creds)

sheet_id = "1Xgv4KfcWfX6irfWJUxEMFjb-lErnWy6UkfAr2aVcCxM"
workbook = client.open_by_key(sheet_id)

worksheet = sh.add_worksheet(title="A worksheet", rows="100", cols="20")
