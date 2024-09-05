from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload
import io
from docx import Document
import os
import time
import random
from oauth2client.service_account import ServiceAccountCredentials
import gspread
import re

# Path to your service account key file
SERVICE_ACCOUNT_FILE = '/Users/g24isha/FormGeneration/credentials1.json'

# Scopes required for Google Drive API
SCOPES = ['https://www.googleapis.com/auth/drive']

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

def ensure_columns(sheet, required_cols):
    # Get current number of columns
    current_cols = len(sheet.row_values(1))
    if current_cols < required_cols:
        # Update the sheet to extend the columns
        new_cols = required_cols - current_cols
        sheet.resize(rows=sheet.row_count, cols=required_cols)

def add_responses(file_name, responses):
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
        
    sheet = spreadsheet.worksheet('post_questions')

    col_num = len(sheet.row_values(1)) + 1
    required_cols = col_num + len(responses)

    # Ensure enough columns are available
    ensure_columns(sheet, required_cols)
    row_num = 2
    for response in responses:
        
        if not execute_with_backoff(sheet.update_cell, 1, col_num, file_name):
            print("Failed to update form ID. Exiting function.")
            return
        if not execute_with_backoff(sheet.update_cell, row_num, col_num, response):
            print("Failed to update answer value. Continuing with next cell.")
        row_num += 1  # Move to the next row for the next question
    col_num += 1
    
    #print(f"Data appended to spreadsheet: {spreadsheet.url}")


             
def list_files_in_folder(folder_id, target_folder_id):
    results = drive_service.files().list(
        q=f"'{folder_id}' in parents",
        fields='files(id, name)').execute()
    items = results.get('files', [])
    x = 0
    y = 0

    if not items:
        print('No files found.')
    else:
        #print('Files:')
        for item in items:
            y += 1
            if y > 35:
            #print(f"{item['name']} ({item['id']})")
                responses = download_file(item['id'], item['name'], target_folder_id)
                if responses:
                    file_name = item['name']
                    index = file_name.rfind(".docx")
                    file_name = file_name[:index]
                    add_responses(file_name, responses)
                x += 1
        print("finished uploading ", x, " files")

def download_file_with_backoff(file_id):
    request = drive_service.files().get_media(fileId=file_id)
    fh = io.BytesIO()
    downloader = MediaIoBaseDownload(fh, request)
    done = False
    while not done:
        status, done = downloader.next_chunk()
    return fh.getvalue()

def upload_file_to_drive(file_path, file_name, target_folder_id):
    index = file_name.rfind(".docx")
    file_metadata = {
        'name': f"{file_name[:index]}.txt",
        'parents': [target_folder_id]
    }
    media = MediaFileUpload(file_path, mimetype='text/plain')
    uploaded_file = drive_service.files().create(body=file_metadata,
                                                 media_body=media,
                                                 fields='id').execute()
    #print(f"Uploaded {file_name}.txt to folder ID: {target_folder_id}")

def download_file(file_id, file_name, target_folder_id):
    try:
        file_content = execute_with_backoff(download_file_with_backoff, file_id)
    except Exception as e:
        print(f"Failed to download file {file_name}: {e}")
        return

    # Save the downloaded file temporarily
    local_file_path = f"{file_name}.docx"
    with open(local_file_path, 'wb') as f:
        f.write(file_content)
    responses = []
    question1 = "Did you already have the idea before this study, or did you come up with the idea on the spot just for our study?"
    question2 = "How many hours did you spend in total on the whole task (including brainstorming and writing down the idea)?"
    question3 = "On a scale of 1 - 5, how difficult is it for you to come up with the idea? (5: Very difficult; 1: Very easy.)"
    question4 = "How does this idea compare to your past research ideas (ideas that you actually worked on)? You can answer with a percentile. E.g., this idea is one of my top 10% ideas."
    contact = "Contact Information:"
    # Extract text from the downloaded .docx file
    doc = Document(local_file_path)
    extracted_text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
    extracted_text_q = re.sub(r'\s+', ' ', extracted_text).strip()
    start = extracted_text.find("Your idea (following the above format):")
    if start == -1:
        print("Files that must be done manually: ", file_name)
        return
    start += 39
    end = extracted_text.find("List of related works that you referred to (leave empty if none):")
    q1 = extracted_text_q.find(question1)
    q2 = extracted_text_q.find(question2)
    q3 = extracted_text_q.find(question3)
    q4 = extracted_text_q.find(question4)
    end_q = extracted_text_q.find(contact)
    responses.append(extracted_text_q[q1+113:q2])
    responses.append(extracted_text_q[q2+108:q3])
    responses.append(extracted_text_q[q3+109:q4])
    responses.append(extracted_text_q[q4+169:end_q])
    extracted_text = extracted_text[start:end].strip()
    
    extracted_text_path = f"{file_name}.txt"
    with open(extracted_text_path, 'w', encoding='utf-8') as f:
        f.write(extracted_text)

    # Upload the .txt file to the target folder
    try:
        execute_with_backoff(upload_file_to_drive, extracted_text_path, file_name, target_folder_id)
    except Exception as e:
        print(f"Failed to upload file {file_name}.txt: {e}")

    # Clean up: delete the downloaded .docx and extracted .txt files
    os.remove(local_file_path)
    os.remove(extracted_text_path)
    return responses


# Replace 'YOUR_FOLDER_ID' and 'TARGET_FOLDER_ID' with the actual folder IDs
folder_id = ''
target_folder_id = ''
list_files_in_folder(folder_id, target_folder_id)