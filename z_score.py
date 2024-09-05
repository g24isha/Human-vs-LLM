from google.oauth2 import service_account
from googleapiclient.discovery import build
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import time
import random
import numpy as np

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
forms_service = build('forms', 'v1', credentials=credentials)
sheets_service = build('sheets', 'v4', credentials=credentials)

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

def update_cell_with_backoff(sheet, row, col, value):
    # Implement your exponential backoff logic here
    execute_with_backoff(sheet.update_cell, row, col, value)
    #sheet.update_cell(row, col, value)
    
def get_overall(name, rows):
    #print(params)
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name(SERVICE_ACCOUNT_FILE, scope)
    client = gspread.authorize(creds)
    

# Build the service
    service = build('sheets', 'v4', credentials=credentials)

    SPREADSHEET_ID = ''
    
    sheet_name = 'AllIdeas'
    column = 'I'
    scores = []
    for i in rows:
        #print(rows)
        RANGE_NAME = f'{sheet_name}!{column}{i}'
        result = service.spreadsheets().values().get(
        spreadsheetId=SPREADSHEET_ID,
        range=RANGE_NAME
        ).execute()
        value1 = result.get('values', [])
        #print(value1)
        id = value1[0][0]
        index1 = id.index('/d/')
        index2 = id.index('/edit')
        id = id[index1+3:index2]
    
        
        NAME_RANGE = 'Form Responses 1!B:B'
        responses_sheet = 'Form Responses 1'
        overall_col = 'Q'
        result3 = service.spreadsheets().values().get(
        spreadsheetId=id,
        range=NAME_RANGE
        ).execute()
        value3 = result3.get('values', [])
        respondents = [item[0].strip().lower() for item in value3]
        #print(respondents)
        #print(respondents)
        #print(name)
        try:
            response_row = respondents.index(name) + 1
        
            OVERALL_RANGE = f'{responses_sheet}!{overall_col}{response_row}'
            result4 = service.spreadsheets().values().get(
            spreadsheetId=id,
            range=OVERALL_RANGE
            ).execute()
            value4 = result4.get('values', [])
            overalls = [item[0].strip().lower() for item in value4]
            #print(overalls)
            score = int(overalls[0][0])
            scores.append(score)
        except ValueError:
            pass  # Handle cases where the 
        
    scores = np.array(scores)
    mean = np.mean(scores)
    std_dev = np.std(scores, ddof=0)  # ddof=0 for population std deviation

# Compute Z-scores
    # print(scores)
    # print(mean)
    # print(std_dev)
    if std_dev == 0:
        # All z-scores will be 0 if there's no variation
        z_scores = [0] * len(scores)
    else:
        z_scores = (scores - mean) / std_dev

    return z_scores

client = gspread.authorize(credentials)
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
      
SPREADSHEET_ID = ''

RANGE_NAME1 = 'AllIdeas!F:F'
RANGE_NAME2 = 'AllIdeas!G:G'
RANGE_NAME3 = 'AllIdeas!H:H'
sheet1 = spreadsheet.worksheet('AllIdeas')
result = sheets_service.spreadsheets().values().get(
    spreadsheetId=SPREADSHEET_ID,
    range=RANGE_NAME1
).execute()
result2 = sheets_service.spreadsheets().values().get(
    spreadsheetId=SPREADSHEET_ID,
    range=RANGE_NAME2
).execute()
result3 = sheets_service.spreadsheets().values().get(
    spreadsheetId=SPREADSHEET_ID,
    range=RANGE_NAME3
).execute()

# Get the values
#this is name of reviewer
reviewer1 = result.get('values', [])
reviewer2 = result2.get('values', [])
reviewer3 = result3.get('values', [])
#print(reviewer1)
names1 = []
names2 = []
names3 = []
for item in reviewer1:
    if len(item) == 0:
        names1.append('none')
    else:
        names1.append(item[0].strip().lower())
names1.pop(0)
for item in reviewer2:
    if len(item) == 0:
        names2.append('none')
    else:
        names2.append(item[0].strip().lower())
names2.pop(0)
for item in reviewer3:
    if len(item) == 0:
        names3.append('none')
    else:
        names3.append(item[0].strip().lower())
names3.pop(0)

# print(names1)
# print(names2)
# print(names3)
scorers = {}
scorers_rows = {}
row_num = 2
x = 0
for name in names1:
    # if x >= 1:
    #     break
    # x += 1
    if name == 'none':
        row_num += 1
        continue
    parentheses = name.find('(')
    if parentheses != -1:
        new_name = name[:parentheses-1]
    if new_name not in scorers: 
        #basically find all the other ideas
        #this person is reviewing and get their
        #overall scores
        print("NAME: ", new_name)
        
        scorers_rows[new_name] = []
        scorers_rows[new_name].append(row_num)
        try:
            index = names1.index(name, row_num) + 2
            scorers_rows[new_name].append(index)
        except ValueError:
            #print('error')
            pass
        try:
            index = names2.index(name, 0) + 2
            scorers_rows[new_name].append(index)
        except ValueError:
            #print('error')
            pass
        try:
            index = names3.index(name, 0) + 2
            scorers_rows[new_name].append(index)
        except ValueError:
            #print('error')
            pass
        print("ROWS: ", scorers_rows[new_name])
        z_scores = get_overall(new_name, scorers_rows[new_name])
        scorers[new_name] = z_scores
        col_num = 18
        column = 'R'
        for i in range (0, len(z_scores)):
            
            responses_sheet = 'AllIdeas'
            RANGE_NAME = f'{responses_sheet}!{column}{scorers_rows[new_name][i]}'
            result = sheets_service.spreadsheets().values().get(
                spreadsheetId=SPREADSHEET_ID,
                range=RANGE_NAME
            ).execute()

            # Retrieve the value
            values = result.get('values', [])

            if not values or not values[0]:
                # print("Cell is empty.")
                # print(z_scores)
                # print(scorers_rows[new_name][i])
                update_cell_with_backoff(sheet1, scorers_rows[new_name][i], col_num, z_scores[i])
            else:
                col_num += 1
                if col_num == 19:
                    column = 'S'
                elif col_num == 20:
                    column = 'T'

        row_num += 1