from google.oauth2 import service_account
from googleapiclient.discovery import build
import gspread
import time
import random
from googleapiclient.errors import HttpError

SERVICE_ACCOUNT_FILE = '/Users/g24isha/FormGeneration/credentials1.json'

# Scopes required for Google Drive and Forms API
SCOPES = [
    'https://www.googleapis.com/auth/drive',
    'https://www.googleapis.com/auth/forms.body'
]

# Authenticate and create the service
credentials = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE, scopes=SCOPES)
drive_service = build('drive', 'v3', credentials=credentials)

MAX_RETRIES = 6
INITIAL_DELAY = 1
MAX_DELAY = 60

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

SPREADSHEET_ID = ''
AUTHORS = 'AllIdeas!B10:B148'
NAMES = 'AllIdeas!C10:C148'
FOLDER_ID = ''

TOTAL = 78

credentials = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE, scopes=SCOPES)
service = build('sheets', 'v4', credentials=credentials)
client = gspread.authorize(credentials)

result1 = execute_with_backoff(service.spreadsheets().values().get, spreadsheetId=SPREADSHEET_ID, range=AUTHORS)
authors_list = result1.get('values', [])

result2 = execute_with_backoff(service.spreadsheets().values().get, spreadsheetId=SPREADSHEET_ID, range=NAMES)
names_list = result2.get('values', [])


results = drive_service.files().list(
    q=f"'{FOLDER_ID}' in parents",
    spaces='drive',
    fields='nextPageToken, files(id, name)').execute()
items = results.get('files', [])
print(len(items))

for item in items:
    file_name = item['name'].strip()
    index = file_name.find('.')
    file_name = file_name[:index]
    found = False
    for i in range(len(authors_list)):
        if not found:
            author = authors_list[i][0].strip()
            if author == 'AI + Human' or author == 'AI + Human (Dup)':
                name = names_list[i][0].strip()
                if name.find(file_name) != -1:
                    found = True
           
    if not found:
        print("unused AI + human idea: ", file_name)