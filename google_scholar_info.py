from google.oauth2 import service_account
from googleapiclient.discovery import build
import gspread
import time
import random
from scholarly import scholarly

# Set up Google Sheets API credentials
SERVICE_ACCOUNT_FILE = '/Users/g24isha/FormGeneration/credentials1.json'
SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',  
    'https://www.googleapis.com/auth/drive'         
]

# Authenticate and create the service
credentials = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE, scopes=SCOPES)
service = build('sheets', 'v4', credentials=credentials)
client = gspread.authorize(credentials)


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

# Function to extract information using BeautifulSoup
def get_scholar_metrics(url):
    try:
        author = scholarly.search_author_id(url.split('user=')[1].split('&')[0])
        scholarly.fill(author)
        num_papers = len(author['publications'])
        citations = author['citedby']
        h_index = author['hindex']
        i10_index = author['i10index']
        return num_papers, citations, h_index, i10_index
    except Exception as e:
        print(f"Error processing {url}: {e}")
        return None, None, None, None


SPREADSHEET_ID = ''
spreadsheet_title = 'All Ideas Info'
  
  #change this range, worksheet name, and colummns for appending data when doing reviewers vs. idea creators
URLS = 'humanInfo!L2:L79'

result = execute_with_backoff(service.spreadsheets().values().get, spreadsheetId=SPREADSHEET_ID, range=URLS)
urls = result.get('values', [])

row_num = 2
data = []
counter = 0
for i in range(len(urls)): 
    # if counter > 3:
    #     break
    # counter += 1
    if len(urls[i]) == 0:
        row_num += 1
        continue
    else:
        url = urls[i][0].strip()
        print(url)
        num_papers, citations, h_index, i10_index = get_scholar_metrics(url)
        data.append([row_num, num_papers, citations, h_index, i10_index])
        row_num += 1
        
print(data)
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

for row, papers, citations, h_index, i10_index in data:
    update_cell_with_backoff(sheet1, row, 13, papers)
    update_cell_with_backoff(sheet1, row, 14, citations)
    update_cell_with_backoff(sheet1, row, 15, h_index)
    update_cell_with_backoff(sheet1, row, 16, i10_index)

