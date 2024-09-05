from google.oauth2 import service_account
from googleapiclient.discovery import build
from google.oauth2 import service_account
from googleapiclient.discovery import build
import time
import random
from googleapiclient.errors import HttpError
import gspread

MAX_RETRIES = 8
INITIAL_DELAY = 1
MAX_DELAY = 100

def exponential_backoff(retry_count):
    return min(MAX_DELAY, INITIAL_DELAY * (2 ** retry_count) + random.uniform(0, 1))

def execute_with_backoff(func, *args, **kwargs):
    retry_count = 0
    while retry_count < MAX_RETRIES:
        try:
            result = func(*args, **kwargs)
            if callable(getattr(result, 'execute', None)):
                result = result.execute()
            return result
        except HttpError as e:
            print(f"HTTP Error: {e}")
            if 'Quota exceeded' in str(e) or 'User rate limit exceeded' in str(e):
                retry_count += 1
                delay = exponential_backoff(retry_count)
                print(f"Quota exceeded, retrying in {delay:.2f} seconds... (attempt {retry_count}/{MAX_RETRIES})")
                time.sleep(delay)
            else:
                print(f"HTTP Exception: {e}")
                raise e
        except TimeoutError as e:
            retry_count += 1
            delay = exponential_backoff(retry_count)
            print(f"Timeout error, retrying in {delay:.2f} seconds... (attempt {retry_count}/{MAX_RETRIES})")
            time.sleep(delay)
        except Exception as e:
            print(f"Exception: {e}")
            raise e
    print(f"Failed after {MAX_RETRIES} retries.")
    return None

def update_cell_with_backoff(sheet, row, col, value):
    # Implement your exponential backoff logic here
    execute_with_backoff(sheet.update_cell, row, col, value)
    

# Replace with your credentials JSON file path
SERVICE_ACCOUNT_FILE = '/Users/g24isha/FormGeneration/credentials1.json'

# Scopes required for Google Sheets API
SCOPES = [
    'https://www.googleapis.com/auth/drive'
]

SPREADSHEET_ID = ''
INSTITUTION = 'humanInfo!J2:J79'
POSITION = 'humanInfo!K2:K79'

TOTAL = 78

credentials = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE, scopes=SCOPES)
service = build('sheets', 'v4', credentials=credentials)
client = gspread.authorize(credentials)

result1 = execute_with_backoff(service.spreadsheets().values().get, spreadsheetId=SPREADSHEET_ID, range=INSTITUTION)
institution_list = result1.get('values', [])

result2 = execute_with_backoff(service.spreadsheets().values().get, spreadsheetId=SPREADSHEET_ID, range=POSITION)
position_list = result2.get('values', [])

institutions = {}

for i in range(TOTAL):
    inst = institution_list[i][0].strip()
    if inst not in institutions:
        institutions[inst] = 1
    else:
        old = institutions[inst]
        institutions[inst] = old + 1

positions = {}

for i in range(TOTAL):
    pos = position_list[i][0].strip()
    if pos not in positions:
        positions[pos] = 1
    else:
        old = positions[pos]
        positions[pos] = old + 1
    

spreadsheet_title = 'All Ideas Info' 
try:
    spreadsheet = execute_with_backoff(client.open, spreadsheet_title)
    if spreadsheet is None:
        print("Failed to open or create spreadsheet.")
       
except gspread.SpreadsheetNotFound:
    # If spreadsheet not found, create a new one
    spreadsheet = execute_with_backoff(client.create, spreadsheet_title)
    if spreadsheet is None:
        print("Failed to open or create spreadsheet.")
    
sheet1 = spreadsheet.worksheet('humanInfo')
print(institutions)
print(positions)
row_num = 32
for key, value in institutions.items():
    update_cell_with_backoff(sheet1, row_num, 1, key)
    update_cell_with_backoff(sheet1, row_num, 2, value)
    update_cell_with_backoff(sheet1, row_num, 3, round(value/TOTAL*100, 2))
    row_num += 1
    
row_num = 32
for key, value in positions.items():
    update_cell_with_backoff(sheet1, row_num, 4, key)
    update_cell_with_backoff(sheet1, row_num, 5, value)
    update_cell_with_backoff(sheet1, row_num, 6, round(value/TOTAL*100, 2))
    row_num += 1
    
    
print('finished')
        

