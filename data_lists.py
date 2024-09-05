from google.oauth2 import service_account
from googleapiclient.discovery import build
import time
import random
import json
from googleapiclient.errors import HttpError
import httplib2
import re

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

#create lists of scores, topics, and reviewers
SPREADSHEET_ID_2 = ''
TOPICS_RANGE = 'AllIdeas!A:A'
CONDITIONS_RANGE = 'AllIdeas!B:B'
RESPONSES_RANGE = 'AllIdeas!I:I'

result = execute_with_backoff(sheets_service.spreadsheets().values().get, spreadsheetId=SPREADSHEET_ID, range=TOPICS_RANGE)
result2 = execute_with_backoff(sheets_service.spreadsheets().values().get, spreadsheetId=SPREADSHEET_ID, range=CONDITIONS_RANGE)
result3 = execute_with_backoff(sheets_service.spreadsheets().values().get, spreadsheetId=SPREADSHEET_ID, range=RESPONSES_RANGE)


# Get the values
#this is name of reviewer
topic_results = result.get('values', [])
conditions_results = result2.get('values', [])
responses_results = result3.get('values', [])


topics = []
conditions = []

reviewers = []
institutions = [] 
contacts = []
consent_responses = []
confirm = []
familiarity = []
reviewed_b4 = []
novelty_scores = []
novelty_ft  = []
feasability_scores = []
feasability_ft = []
effective_scores = []
effective_ft = []
excite_scores = []
excite_ft = []
scores = []
overall_ft = []
confidence = []
time_spent = []

RANGES = {
    'affiliation' : 'Form Responses 1!C:C',
    'email' : 'Form Responses 1!D:D',
    'consent' : 'Form Responses 1!E:E',
    'noAI' : 'Form Responses 1!F:F',
    'familiar' : 'Form Responses 1!G:G',
    'major_conf' : 'Form Responses 1!H:H',
    'novelty_scores': 'Form Responses 1!I:I',
    'nft': 'Form Responses 1!J:J',
    'feasability_scores': 'Form Responses 1!K:K',
    'fft': 'Form Responses 1!L:L',
    'effective_scores': 'Form Responses 1!M:M',
    'eft': 'Form Responses 1!N:N',
    'excite_scores': 'Form Responses 1!O:O',
    'exft': 'Form Responses 1!P:P',
    'overall_scores': 'Form Responses 1!Q:Q',
    'oft': 'Form Responses 1!R:R',
    'conf' : 'Form Responses 1!S:S',
    'mins' : 'Form Responses 1!T:T'
}

for i in range(1, len(topic_results)):
    if len(responses_results[i]) == 0:
        continue
    topic = topic_results[i][0]
    hashtag = topic.find('#')
    topic = topic[:hashtag-1]
    
    author = conditions_results[i][0]
    if author.strip().lower() == 'ai + ai':
        condition = 'AI + AI'
    elif author.find('AI + Human') != -1:
        condition = 'AI + Human'
    else:
        condition = 'Human'
        
    id = responses_results[i][0]
    first_index = id.find('/d/')
    second_index = id.find('/edit')
    id = id[first_index+3:second_index]
    
    NAMES_RANGE = 'Form Responses 1!B:B'

    result4 = execute_with_backoff(sheets_service.spreadsheets().values().get, spreadsheetId=id, range=NAMES_RANGE)
    
    names = result4.get('values', [])
    if len(names) == 1:
        continue
    
    data = {}
    for key, range_name in RANGES.items():
        result = execute_with_backoff(sheets_service.spreadsheets().values().get, spreadsheetId=id, range=range_name)
        data[key] = result.get('values', [])

    
    
    for j in range(1, len(names)):
        topics.append(topic)
        conditions.append(condition)
        
        reviewers.append(names[j][0].strip())
        institutions.append(data['affiliation'][j][0].strip())
        contacts.append(data['email'][j][0].strip())
        consent_responses.append(data['consent'][j][0].strip())
        confirm.append(data['noAI'][j][0].strip())
        familiarity.append(data['familiar'][j][0].strip())
        reviewed_b4.append(data['major_conf'][j][0].strip())
        novelty_scores.append(int(data['novelty_scores'][j][0][0]))
        novelty_ft.append(data['nft'][j][0].strip())
        feasability_scores.append(int(data['feasability_scores'][j][0][0]))
        feasability_ft.append(data['fft'][j][0].strip())
        effective_scores.append(int(data['effective_scores'][j][0][0]))
        effective_ft.append(data['eft'][j][0].strip())
        excite_scores.append(int(data['excite_scores'][j][0][0]))
        excite_ft.append(data['exft'][j][0].strip())
        scores.append(int(data['overall_scores'][j][0][0]))
        overall_ft.append(data['oft'][j][0].strip())
        confidence.append(data['conf'][j][0].strip())
        mins = data['mins'][j][0]
        match = re.match(r'^\d+', mins)
        if match:
            time_spent.append(int(match.group()))
    

       
        
       
        
        
        


save_dict = {
    'topics': topics,
    'conditions': conditions,
    'reviewers': reviewers,
    'institutions' : institutions,
    'emails' : contacts,
    'consent' : consent_responses,
    'no AI use' : confirm,
    'familiarity with topic' : familiarity,
    'reviewed for conferences' : reviewed_b4,
    'novelty scores' : novelty_scores,
    'novelty free-text' : novelty_ft,
    'feasability scores' : feasability_scores,
    'feasability free-text' : feasability_ft,
    'effective scores' : effective_scores, 
    'effective free-text' : effective_ft, 
    'excitement scores' : excite_scores, 
    'excitement free-text' : excite_ft, 
    'overall scores': scores,
    'overall free-text' : overall_ft,
    'confidence' : confidence, 
    'minutes spent' : time_spent
    
}
with open("data_points.json", "w") as outfile:
    json.dump(save_dict, outfile, indent=4)