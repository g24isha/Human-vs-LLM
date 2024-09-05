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

def get_ids():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name(SERVICE_ACCOUNT_FILE, scope)
    client = gspread.authorize(creds)
        
    # Build the service
    service = build('sheets', 'v4', credentials=credentials)
    spreadsheet_title = 'All Ideas Info' 
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
    SPREADSHEET_ID = ''
    RANGE_NAME = 'AllIdeas!I:I'

    
    #this is for the ids

    
    result = execute_with_backoff(service.spreadsheets().values().get, spreadsheetId=SPREADSHEET_ID, range=RANGE_NAME)

        # Get the values
    values = result.get('values', [])

    ids = []
    names = []
    info = []
    row_nums = []
    row = 2
    
    for i in range (1, len(values)):
        
        if not values[i]:
            row += 1
        else:
            id = values[i][0]
            #name = values2[i][0]
            row_nums.append(row)
            index1 = id.find('/d/') + 3
            index2 = id.find('/edit')
            if index1 != -1 and index2 != -1:
                id = id[index1:index2]
                #print(id)
                ids.append(id)
            row += 1
            
    
    return row_nums, ids


def get_overall(id):

    service = build('sheets', 'v4', credentials=credentials)
 
    RANGE_NAME2 = 'Form Responses 1!Q:Q'

    
    result2 = execute_with_backoff(service.spreadsheets().values().get, spreadsheetId=id, range=RANGE_NAME2)
    # Get the values

    #this is overall score
    values2 = result2.get('values', [])
    #print(values)
    scores = []
    for i in range (1, len(values2)):
        score = int(values2[i][0][0])
        scores.append(score)
    return scores



    
def update_cell_with_backoff(sheet, row, col, value):
    # Implement your exponential backoff logic here
    execute_with_backoff(sheet.update_cell, row, col, value)
    #sheet.update_cell(row, col, value)
    
def create_spreadsheet(file_data):
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name(SERVICE_ACCOUNT_FILE, scope)
    client = gspread.authorize(creds)
    

# Build the service
    service = build('sheets', 'v4', credentials=credentials)
    spreadsheet_title = 'All Ideas Info' 
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
    sheet1 = spreadsheet.sheet1
    
    for row, num_responses, mean, std_dev in file_data:
        update_cell_with_backoff(sheet1, row, 10, num_responses)
        update_cell_with_backoff(sheet1, row, 11, mean)
        update_cell_with_backoff(sheet1, row, 12, std_dev)
        
    print(f"Data appended to spreadsheet: {spreadsheet.url}")


def get_avg_overall():
  
# Build the service
    service = build('sheets', 'v4', credentials=credentials)
    SPREADSHEET_ID = ''
    RANGE_NAME = 'AllIdeas!B:B'
    RANGE2_NAME = 'AllIdeas!J:J'
    RANGE3_NAME = 'AllIdeas!K:K'

    result = execute_with_backoff(service.spreadsheets().values().get, spreadsheetId=SPREADSHEET_ID, range=RANGE_NAME)
    result2 = execute_with_backoff(service.spreadsheets().values().get, spreadsheetId=SPREADSHEET_ID, range=RANGE2_NAME)
    result3 = execute_with_backoff(service.spreadsheets().values().get, spreadsheetId=SPREADSHEET_ID, range=RANGE3_NAME)
    
    names = result.get('values', [])
    num_responses = result2.get('values', [])
    means = result3.get('values', [])
    
    print(len(names))
    print(len(num_responses))
    print(len(means))
    
    AI_sum = 0
    AI_number = 0
    human_sum = 0
    human_number = 0
    AI_human_sum  = 0
    AI_human_number = 0

    for i in range(1, len(means)):
        #num_responses*mean added to overall sum
        #num_responses added to overall number
        if len(num_responses[i]) == 0:
            continue
        if names[i][0].strip() == 'AI + AI':
            AI_sum += int(num_responses[i][0])
            AI_number += int(num_responses[i][0])*float(means[i][0])
        elif names[i][0].find('AI + Human') != -1:
            AI_human_sum += int(num_responses[i][0])
            AI_human_number += int(num_responses[i][0])*float(means[i][0])
        else:
            human_sum += int(num_responses[i][0])
            human_number += int(num_responses[i][0])*float(means[i][0])
    print("human overall avg: ", round(human_number/human_sum, 2))
    print("AI overall avg: ", round(AI_number/AI_sum, 2))
    print("human + AI overall avg: ", round(AI_human_number/AI_human_sum, 2))
    print("number of human responses: ", human_sum)
    print("number of AI responses: ", AI_sum)
    print("number of human + AI responses: ", AI_human_sum)
    

#have to change x and counter upper bound when redoing it
x = 0
#upper bound of counter is set to x - 1 when updating spreadsheet
counter = 0
row_nums, ids = get_ids()

#print(spreadsheet_ids)
spreadsheet_data = []
for i in range(len(row_nums)):
    # counter += 1
    # if counter < 22:
    #     continue
    try:
        # Attempt to call get_overall and process the results
        scores = get_overall(ids[i])
        
        # Check if scores is empty and append appropriate data
        if len(scores) == 0:
            spreadsheet_data.append([row_nums[i], 0, 0, 0])
        else:
            spreadsheet_data.append([row_nums[i], len(scores), np.mean(scores), np.std(scores)])
    
    except Exception as e:
        # Handle the error by printing it and exiting the loop
        print(f"An error occurred for spreadsheet ID {ids[i]}: {e}")
        break  # Exit the loop if an error occurs
    
    finally:
        # Increment the counter regardless of whether an error occurred
        x += 1

    
    
    
create_spreadsheet(spreadsheet_data)
print("number of responses: ", x)

get_avg_overall()





#for each spreadsheet, find number of non-empty rows 
#then if the number of rows is more than 1, get the 
# overall score (column Q, will have to get 0th index
# for numerical response)
#enter number of responses in column P of original
#spreadsheet, mean of overall in column Q, and std
#dev. of overall scores in column R
#also keep track of row number throughout the loop
