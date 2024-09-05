from google.oauth2 import service_account
from googleapiclient.discovery import build
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import time
import random



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
    RANGE_NAME = 'AllIdeas!K:K'
    sheet1 = spreadsheet.sheet1
    result = service.spreadsheets().values().get(
        spreadsheetId=SPREADSHEET_ID,
        range=RANGE_NAME
    ).execute()

        # Get the values
    values = result.get('values', [])
    ids = []
    for x in values:
        for y in x:
            index1 = y.find('/d/') + 3
            index2 = y.find('/edit')
            if index1 != -1 and index2 != -1:
                y = y[index1:index2]
                ids.append(y)
    return ids

ids = get_ids()
x = 0
for id in ids:
    form = forms_service.forms().get(formId=id).execute()
    question_index = 16  
    option_index = 6  
    
    index2 = 8
    index3 = 9
    index4 = 11
    index5 = 13
    index6 = 15
    index7 = 17

    # Assuming you want to update the first question
    first_question_id = form['items'][question_index]['itemId']
    
    question_item = form['items'][question_index]
    question_id = question_item['itemId']
    
    question_item2 = form['items'][index2]
    question2_id = question_item2['itemId']
    
    question_item3 = form['items'][index3]
    question3_id = question_item3['itemId']
    
    question4_id = form['items'][index4]['itemId']
    question5_id = form['items'][index5]['itemId']
    question6_id = form['items'][index6]['itemId']
    question7_id = form['items'][index7]['itemId']

    # Get the options of the 17th question
    options = question_item['questionItem']['question']['choiceQuestion']['options']

    # Update the 7th option
    options[option_index]['value'] = '7 (Good idea, would be accepted by major AI conferences)'

    # Define the request to update the 7th option of the 17th question
    requests = [
        {
            'updateItem': {
                'item': {
                    'itemId': question_id,
                    'questionItem': {
                        'question': {
                            'choiceQuestion': {
                                'options': options
                            }
                        }
                    }
                },
                'location': {
                'index': question_index
                },
                'updateMask': 'questionItem.question.choiceQuestion.options'
            }
        },
        {
            'updateItem': {
                'item': {
                    'itemId': question2_id,
                    'title': "𝐍𝐨𝐯𝐞𝐥𝐭𝐲: Whether the idea is creative and different from existing works on the topic, and brings fresh insights. You are encouraged to search for related works online. You should consider all papers that appeared online prior to July 2024 as existing work when judging the novelty.",
                    'questionItem': form['items'][index2]['questionItem']
                },
                'location': {
                    'index': index2
                },
                'updateMask': 'title'
            }
        },
        {
            'updateItem': {
                'item': {
                    'itemId': question3_id,
                    'title': "Free-Text Rationale: Short justification for your score. If you give a low score, you should specify similar related works. (Your rationale should be at least 2-3 sentences.)",
                    'questionItem': form['items'][index3]['questionItem']
                },
                'location': {
                    'index': index3
                },
                'updateMask': 'title'
            }
        },
        {
            'updateItem': {
                'item': {
                    'itemId': question4_id,
                    'title': "Free-Text Rationale: Short justification for your score. If you give a low score, you should specify what parts are difficult to execute and why. (Your rationale should be at least 2-3 sentences.)",
                    'questionItem': form['items'][index4]['questionItem']
                },
                'location': {
                    'index': index4
                },
                'updateMask': 'title'
            }
        },
        {
            'updateItem': {
                'item': {
                    'itemId': question5_id,
                    'title': "Free-Text Rationale: Short justification for your score. (Your rationale should be at least 2-3 sentences.)",
                    'questionItem': form['items'][index5]['questionItem']
                },
                'location': {
                    'index': index5
                },
                'updateMask': 'title'
            }
        },
        {
            'updateItem': {
                'item': {
                    'itemId': question6_id,
                    'title': "Free-Text Rationale: Short justification for your score. (Your rationale should be at least 2-3 sentences.)",
                    'questionItem': form['items'][index6]['questionItem']
                },
                'location': {
                    'index': index6
                },
                'updateMask': 'title'
            }
        },
        {
            'updateItem': {
                'item': {
                    'itemId': question7_id,
                    'title':"You should also provide a rationale for your overall score (Your rationale should be at least 2-3 sentences.):",
                    'questionItem': form['items'][index7]['questionItem']
                },
                'location': {
                    'index': index7
                },
                'updateMask': 'title'
            }
        }
    ]


# Send the update request
    result = forms_service.forms().batchUpdate(formId=id, body={'requests': requests}).execute()
    #print('Form updated successfully:', result)
    x += 1
print("number of forms updated: ", x)