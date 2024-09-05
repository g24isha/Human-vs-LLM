from google.oauth2 import service_account
from googleapiclient.discovery import build
from google.oauth2 import service_account
from googleapiclient.discovery import build
import time
import random
from googleapiclient.errors import HttpError
import json

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

# Replace with your credentials JSON file path
SERVICE_ACCOUNT_FILE = '/Users/g24isha/FormGeneration/credentials1.json'

# Scopes required for Google Sheets API
SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']

# Replace with your Google Sheets ID and desired range
FILE_NAME_TO_ID = ''
NAMES = 'post_questions!B1:AY1'
Q1 = 'post_questions!B2:AY2'
Q2 = 'post_questions!B3:AY3'
Q3 = 'post_questions!B4:AY4'
Q4 = 'post_questions!B5:AY5'
Q5 = 'post_questions!B6:AY6'


# Authenticate and create the service
credentials = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE, scopes=SCOPES)
service = build('sheets', 'v4', credentials=credentials)


result1 = execute_with_backoff(service.spreadsheets().values().get, spreadsheetId=FILE_NAME_TO_ID, range=NAMES)
name_list = result1.get('values', [])[0]

result2 = execute_with_backoff(service.spreadsheets().values().get, spreadsheetId=FILE_NAME_TO_ID, range=Q1)
question1_list = result2.get('values', [])[0]

result3 = execute_with_backoff(service.spreadsheets().values().get, spreadsheetId=FILE_NAME_TO_ID, range=Q2)
question2_list = result3.get('values', [])[0]

result4 = execute_with_backoff(service.spreadsheets().values().get, spreadsheetId=FILE_NAME_TO_ID, range=Q3)
question3_list = result4.get('values', [])[0]

result5 = execute_with_backoff(service.spreadsheets().values().get, spreadsheetId=FILE_NAME_TO_ID, range=Q4)
question4_list = result5.get('values', [])[0]

result6 = execute_with_backoff(service.spreadsheets().values().get, spreadsheetId=FILE_NAME_TO_ID, range=Q5)
question5_list = result6.get('values', [])[0]
    
    
save_dict = {
    'names': name_list,
    'question 1' : question1_list,
    'question 2' : question2_list,
    'question 3' : question3_list, 
    'question 4' : question4_list,
    'familiarity' : question5_list
}

with open("post_questions.json", "w") as outfile:
    json.dump(save_dict, outfile, indent=4)