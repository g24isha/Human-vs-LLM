from google.oauth2 import service_account
from googleapiclient.discovery import build
import time
import random
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# Authenticate using a service account key file
SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly', 'https://www.googleapis.com/auth/forms.responses.readonly']
SERVICE_ACCOUNT_FILE = '/Users/g24isha/FormGeneration/credentials1.json'

credentials = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE, scopes=SCOPES)

sheets_service = build('sheets', 'v4', credentials=credentials)
forms_service = build('forms', 'v1', credentials=credentials)

SPREADSHEET_ID = ''
RANGE_NAME = 'Sheet1!M:AD'  # Adjust the range to match where your form IDs are

MAX_RETRIES = 6
INITIAL_DELAY = 1
MAX_DELAY = 60

def exponential_backoff(retry_count):
    return min(MAX_DELAY, INITIAL_DELAY * (2 ** retry_count) + random.uniform(0, 1))

def execute_with_backoff(func, *args, **kwargs):
    retry_count = 0
    while retry_count < MAX_RETRIES:
        try:
            return func(*args, **kwargs)
        except Exception as e:
            if 'Quota exceeded' in str(e):
                retry_count += 1
                delay = exponential_backoff(retry_count)
                print(f"Quota exceeded, retrying in {delay:.2f} seconds... (attempt {retry_count}/{MAX_RETRIES})")
                time.sleep(delay)
            else:
                raise e
    print(f"Failed after {MAX_RETRIES} retries.")
    return None

def get_form_ids():
    result = execute_with_backoff(sheets_service.spreadsheets().values().get, spreadsheetId=SPREADSHEET_ID, range=RANGE_NAME).execute()
    if result is None:
        return []
    rows = result.get('values', [])
    form_data = [(row[0], row[1:]) for row in rows] 
    return form_data

def get_form_responses(form_id):
    response = execute_with_backoff(forms_service.forms().responses().list, formId=form_id).execute()
    if response is None:
        return []
    return response.get('responses', [])

def ensure_columns(sheet, required_cols):
    # Get current number of columns
    current_cols = len(sheet.row_values(1))
    if current_cols < required_cols:
        # Update the sheet to extend the columns
        new_cols = required_cols - current_cols
        sheet.resize(rows=sheet.row_count, cols=required_cols)

def add_responses(form_id, responses, question_order):
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name(SERVICE_ACCOUNT_FILE, scope)
    client = gspread.authorize(creds)
    
    spreadsheet_title = 'fileNameToID'
    try:
        spreadsheet = execute_with_backoff(client.open, spreadsheet_title)
        if spreadsheet is None:
            print("Failed to open or create spreadsheet.")
            return
    except gspread.SpreadsheetNotFound:
        # If spreadsheet not found, create a new one
        spreadsheet = execute_with_backoff(client.create, spreadsheet_title)
        if spreadsheet is None:
            print("Failed to open or create spreadsheet.")
            return
        
    sheet = spreadsheet.worksheet('responses')

    col_num = len(sheet.row_values(1)) + 1
    required_cols = col_num + len(responses)

    # Ensure enough columns are available
    ensure_columns(sheet, required_cols)
    
    for response in responses:
        row_num = 2
        
        if not execute_with_backoff(sheet.update_cell, 1, col_num, form_id):
            print("Failed to update form ID. Exiting function.")
            return

        for question_id in question_order:
            answer_data = response.get('answers', {}).get(question_id, {})
            answer_values = answer_data.get('textAnswers', {}).get('answers', [])
            for answer in answer_values:
                value = answer.get('value', '')
                if not execute_with_backoff(sheet.update_cell, row_num, col_num, value):
                    print("Failed to update answer value. Continuing with next cell.")
                row_num += 1  # Move to the next row for the next question
        col_num += 1
    
    print(f"Data appended to spreadsheet: {spreadsheet.url}")

# Example usage
form_data = get_form_ids()
for form_id, question_ids in form_data:
    responses = get_form_responses(form_id)
    add_responses(form_id, responses, question_ids)