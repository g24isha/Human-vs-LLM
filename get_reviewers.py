from google.oauth2 import service_account
from googleapiclient.discovery import build
import time
import random
from googleapiclient.errors import HttpError
import httplib2
import gspread

#change this to the location of your credentials1.json file 
SERVICE_ACCOUNT_FILE = '/Users/g24isha/FormGeneration/credentials1.json'

# Scopes required for Google Drive and Forms API
SCOPES = [
    'https://www.googleapis.com/auth/drive',
    'https://www.googleapis.com/auth/forms.body'
]

# Authenticate and create the service
credentials = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE, scopes=SCOPES)
client = gspread.authorize(credentials)
http = httplib2.Http(timeout=120)
drive_service = build('drive', 'v3', credentials=credentials)
forms_service = build('forms', 'v1', credentials=credentials)
sheets_service = build('sheets', 'v4', credentials=credentials)

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
    execute_with_backoff(sheet.update_cell, row, col, value)
    
SPREADSHEET_ID = ''

REVIEWERS1_RANGE = 'AllIdeas!F:F'
REVIEWERS2_RANGE = 'AllIdeas!G:G'
REVIEWERS3_RANGE = 'AllIdeas!H:H'
CURRENT_RANGE = 'humanInfo!I:I'

result1 = execute_with_backoff(sheets_service.spreadsheets().values().get, spreadsheetId=SPREADSHEET_ID, range=REVIEWERS1_RANGE)
result2 = execute_with_backoff(sheets_service.spreadsheets().values().get, spreadsheetId=SPREADSHEET_ID, range=REVIEWERS2_RANGE)
result3 = execute_with_backoff(sheets_service.spreadsheets().values().get, spreadsheetId=SPREADSHEET_ID, range=REVIEWERS3_RANGE)
result4 = execute_with_backoff(sheets_service.spreadsheets().values().get, spreadsheetId=SPREADSHEET_ID, range=CURRENT_RANGE)

reviewers1 = result1.get('values', [])
reviewers2 = result2.get('values', [])
reviewers3 = result3.get('values', [])
current_reviewers = result4.get('values', [])

reviewers = []
# print(current_reviewers)
for i in range(1, len(current_reviewers)):
    if len(current_reviewers[i]) != 0:
        reviewers.append(current_reviewers[i][0].strip())
        
start = len(reviewers)

for i in range(1, len(reviewers1)):
    if reviewers1[i]:
        name = reviewers1[i][0].strip()
        parentheses = name.find('(')
        if parentheses != -1:
            name = name[:parentheses - 1]
        if name not in reviewers:
            reviewers.append(name)

for i in range(1, len(reviewers2)):
    if reviewers2[i]:
        name = reviewers2[i][0].strip()
        parentheses = name.find('(')
        if parentheses != -1:
            name = name[:parentheses - 1]
        if name not in reviewers:
            reviewers.append(name)
            
            
for i in range(1, len(reviewers3)):
    if reviewers3[i]:
        name = reviewers3[i][0].strip()
        parentheses = name.find('(')
        if parentheses != -1:
            name = name[:parentheses - 1]
        if name not in reviewers:
            reviewers.append(name)

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
#print (reviewers)
row_num = 76
for i in range (start, len(reviewers)):
    update_cell_with_backoff(sheet1, row_num, 9, reviewers[i])
    row_num += 1