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
    # Implement your exponential backoff logic here
    execute_with_backoff(sheet.update_cell, row, col, value)

spreadsheet_title = 'All Ideas Info'
SPREADSHEET_ID = ''
REVIEWERS = 'humanInfo!I2:I80'
AUTHORS = 'AllIdeas!B2:B148'
TOPICS = 'AllIdeas!A2:A148'
REVIEWERS1 = 'AllIdeas!F2:F148'
REVIEWERS2 = 'AllIdeas!G2:G148'
REVIEWERS3 = 'AllIdeas!H2:H148'



result1 = execute_with_backoff(sheets_service.spreadsheets().values().get, spreadsheetId=SPREADSHEET_ID, range=REVIEWERS)
reviewers_list = result1.get('values', [])

result2 = execute_with_backoff(sheets_service.spreadsheets().values().get, spreadsheetId=SPREADSHEET_ID, range=AUTHORS)
authors_list = result2.get('values', [])

result3 = execute_with_backoff(sheets_service.spreadsheets().values().get, spreadsheetId=SPREADSHEET_ID, range=REVIEWERS1)
reviewers1_list = result3.get('values', [])

result4 = execute_with_backoff(sheets_service.spreadsheets().values().get, spreadsheetId=SPREADSHEET_ID, range=REVIEWERS2)
reviewers2_list = result4.get('values', [])

result5 = execute_with_backoff(sheets_service.spreadsheets().values().get, spreadsheetId=SPREADSHEET_ID, range=REVIEWERS3)
reviewers3_list = result5.get('values', [])

result6 = execute_with_backoff(sheets_service.spreadsheets().values().get, spreadsheetId=SPREADSHEET_ID, range=TOPICS)
topics_list = result6.get('values', [])

authors = []
for x in authors_list:
    authors.append(x[0].strip())
    
reviewers1 = []
for x in reviewers1_list:
    if len(x) == 0:
        reviewers1.append('')
    else:
        index = x[0].find('(')
        if index != -1:
            x[0] = x[0][:index - 1]
        reviewers1.append(x[0].strip())
        
reviewers2 = []
for x in reviewers2_list:
    if len(x) == 0:
        reviewers2.append('')
    else:
        index = x[0].find('(')
        if index != -1:
            x[0] = x[0][:index - 1]
        reviewers2.append(x[0].strip())
        
reviewers3 = []
for x in reviewers3_list:
    if len(x) == 0:
        reviewers3.append('')
    else:
        index = x[0].find('(')
        if index != -1:
            x[0] = x[0][:index - 1]
        reviewers3.append(x[0].strip())
    
also_authored = []
num_reviews = []
num_conditions = []
num_topics = []
for x in reviewers_list:
    reviewer = x[0].strip()
    #print(reviewer)
    if reviewer in authors:
        also_authored.append('Y')
    else:
        also_authored.append('N')
    indexes1 = [index for index, value in enumerate(reviewers1) if value.strip() == reviewer]
    indexes2 = [index for index, value in enumerate(reviewers2) if value.strip() == reviewer]
    indexes3 = [index for index, value in enumerate(reviewers3) if value.strip() == reviewer]
    # print(indexes1)
    # print(indexes2)
    # print(indexes3)
    num_reviews.append(len(indexes1) + len(indexes2) + len(indexes3))
    conditions_list = []
    for index in indexes1:
        if authors[index] == 'AI + AI':
            if 'AI + AI' not in conditions_list:
                conditions_list.append('AI + AI')
        elif authors[index].find('AI + Human') != -1:
            if 'AI + Human' not in conditions_list:
                conditions_list.append('AI + Human')
        elif 'Human' not in conditions_list:
            conditions_list.append('Human')
            
    for index in indexes2:
        if authors[index] == 'AI + AI':
            if 'AI + AI' not in conditions_list:
                conditions_list.append('AI + AI')
        elif authors[index].find('AI + Human') != -1:
            if 'AI + Human' not in conditions_list:
                conditions_list.append('AI + Human')
        elif 'Human' not in conditions_list:
            conditions_list.append('Human')
            
    for index in indexes3:
        if authors[index] == 'AI + AI':
            if 'AI + AI' not in conditions_list:
                conditions_list.append('AI + AI')
        elif authors[index].find('AI + Human') != -1:
            if 'AI + Human' not in conditions_list:
                conditions_list.append('AI + Human')
        elif 'Human' not in conditions_list:
            conditions_list.append('Human')
            
    num_conditions.append(len(conditions_list))
    
    topics = []
    for index in indexes1:
        topic = topics_list[index][0].strip()
        hashtag = topic.find('#')
        topic = topic[:hashtag-1]
        if topic not in topics:
            topics.append(topic)
    for index in indexes2:
        topic = topics_list[index][0].strip()
        hashtag = topic.find('#')
        topic = topic[:hashtag-1]
        if topic not in topics:
            topics.append(topic)
            
    for index in indexes3:
        topic = topics_list[index][0].strip()
        hashtag = topic.find('#')
        topic = topic[:hashtag-1]
        if topic not in topics:
            topics.append(topic)
            
    num_topics.append(len(topics))
    
# print(also_authored)
# print(num_reviews)
# print(num_topics)
# print(num_conditions)
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
    
for i in range(len(reviewers_list)):
    if i < 64:
        continue
    update_cell_with_backoff(sheet1, i + 2, 17, also_authored[i])
    update_cell_with_backoff(sheet1, i + 2, 18, num_reviews[i])
    update_cell_with_backoff(sheet1, i + 2, 19, num_topics[i])
    update_cell_with_backoff(sheet1, i + 2, 20, num_conditions[i])
    


    