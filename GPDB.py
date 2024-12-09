from google.oauth2.service_account import Credentials
import gspread

SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
]


# Authenticate with the credentials file and scope
creds = Credentials.from_service_account_file("stlogistics-36de04f6404c.json", scopes=SCOPES)
client = gspread.authorize(creds)

try:
    # Open your Google Sheet
    sheet = client.open("41st Logistics").sheet1
    print(sheet.get_all_records())
except Exception as e:
    print(creds.scopes)

    print(f"Error accessing the Google Sheet: {e}")
