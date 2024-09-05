from google.oauth2 import service_account
from googleapiclient.discovery import build
import io
from googleapiclient.http import MediaIoBaseDownload
import time
import random
import json

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
def read_file_content_with_retry(file_id):
    return execute_with_backoff(read_file_content, file_id)

def read_file_content(file_id):
    request = drive_service.files().get_media(fileId=file_id)
    file_data = io.BytesIO()
    downloader = MediaIoBaseDownload(file_data, request)
    done = False
    while not done:
        status, done = downloader.next_chunk()
    file_data.seek(0)
    raw_data = file_data.read()
    return raw_data.decode('utf-8', errors='replace')

    
HUMAN_IDEAS = ''
AI_IDEAS = ''
AI_HUMAN_IDEAS = ''

# List all files in the folder
result1 = drive_service.files().list(
    q=f"'{HUMAN_IDEAS}' in parents",
    spaces='drive',
    fields='nextPageToken, files(id, name)').execute()
items1 = result1.get('files', [])

result2 = drive_service.files().list(
    q=f"'{AI_IDEAS}' in parents",
    spaces='drive',
    fields='nextPageToken, files(id, name)').execute()
items2 = result2.get('files', [])

result3 = drive_service.files().list(
    q=f"'{AI_HUMAN_IDEAS}' in parents",
    spaces='drive',
    fields='nextPageToken, files(id, name)').execute()
items3 = result3.get('files', [])

print(len(items1))
print(len(items2))
print(len(items3))

human_word_count = []
for item in items1:
        file_id = item['id']
        text = read_file_content_with_retry(file_id).strip()
        num_words = len(text.split())
        human_word_count.append(num_words)
        
AI_word_count = []

for item in items2:
        file_id = item['id']
        text = read_file_content_with_retry(file_id).strip()
        num_words = len(text.split())
        AI_word_count.append(num_words)
        
AI_human_word_count = []

for item in items3:
        file_id = item['id']
        text = read_file_content_with_retry(file_id).strip()
        num_words = len(text.split())
        AI_human_word_count.append(num_words)

save_dict = {
    'human ideas': human_word_count,
    'AI ideas' : AI_word_count,
    'human and AI ideas' : AI_human_word_count
}

with open("word_counts.json", "w") as outfile:
    json.dump(save_dict, outfile, indent=4)