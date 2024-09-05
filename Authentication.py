import os.path
import google.auth
import google.auth.transport.requests
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# If modifying these SCOPES, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/forms.body']

def authenticate():
    """Shows basic usage of the Forms API.
    Prints the titles of the first 10 forms the user has access to.
    """
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.json'):
        creds = google.auth.load_credentials_from_file('token.json')[0]
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(google.auth.transport.requests.Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    return creds

def create_form(service, title, description):
    try:
        # Create a new form
        form = {
            "info": {
                "title": title,
                "description": description,
                "documentTitle": title,
            }
        }
        result = service.forms().create(body=form).execute()
        print(f'Form created with ID: {result["formId"]}')
    except HttpError as error:
        print(f'An error occurred: {error}')
        form = None

def main():
    creds = authenticate()
    try:
        service = build('forms', 'v1', credentials=creds)
        title = "Sample Form"
        descriptions = ["Description 1", "Description 2", "Description 3"]  # Add your descriptions here

        for description in descriptions:
            create_form(service, title, description)

    except HttpError as error:
        print(f'An error occurred: {error}')

if __name__ == '__main__':
    main()
