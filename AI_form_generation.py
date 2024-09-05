from google.oauth2 import service_account
from googleapiclient.discovery import build
import io
from googleapiclient.http import MediaIoBaseDownload
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import time
import random
import chardet


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

# Function to read file content from Google Drive
def read_file_content(file_id):
    request = drive_service.files().get_media(fileId=file_id)
    file_data = io.BytesIO()
    downloader = MediaIoBaseDownload(file_data, request)
    done = False
    while not done:
        status, done = downloader.next_chunk()
    file_data.seek(0)
    raw_data = file_data.read()
    result = chardet.detect(raw_data)
    file = drive_service.files().get(fileId=file_id, fields='webViewLink').execute()
    return file['webViewLink'], raw_data.decode('utf-8', errors='replace')

def read_file_content_with_retry(file_id):
    return execute_with_backoff(read_file_content, file_id)

def create_google_form(experiment_description, topic, link):
    instructions = (
        "𝐈𝐧𝐭𝐫𝐨𝐝𝐮𝐜𝐭𝐢𝐨𝐧:\n"
        """ Welcome to the study! We are a group of researchers from Stanford NLP (PIs: Tatsu Hashimoto & Diyi Yang). We are conducting a research project on empowering the scientific research ideation process with AI.

You are invited to contribute to our study by following the instructions in this form and scoring the given idea along the dimensions of: novelty, feasibility, (expected) effectiveness, and excitement. You will be assigned one randomly selected idea, and you should base your judgment purely on the quality of the ideas, rather than factors like writing style or formatting.

You will be given 5 days to complete this, so take your time and read through the idea carefully. Once you submit this form, we will compensate you for your time by paying $25 for each idea you reviewed. Please also indicate the time you spent on this task at the end of this form for us to better understand the workload. Once you finish, just click submit. 

IRB Information: This project is approved by Stanford IRB (IRB# 74246). If you have read this form and have decided to participate in this project, please understand your participation is voluntary and you have the right to withdraw your consent or discontinue participation at any time without penalty or loss of benefits to which you are otherwise entitled. The alternative is to not participate. You have the right to refuse to answer particular questions. The results of this research study may be presented at scientific or professional meetings or published in scientific journals. Your individual privacy will be maintained in all published and written data resulting from the study.

Questions: If you have any questions, concerns or complaints about this research, its procedures, risks and benefits, contact the Protocol Director: Chenglei Si, clsi@stanford.edu, 240-484-4880.

Independent Contact: If you are not satisfied with how this study is being conducted, or if you have any concerns, complaints, or general questions about the research or your rights as a participant, please contact the Stanford Institutional Review Board (IRB) to speak to someone independent of the research team at 650-723-2480 or toll free at 1-866-680-2906, or email at irbnonmed@stanford.edu. You can also write to the Stanford IRB, Stanford University, 1705 El Camino Real, Palo Alto, CA 94306.

𝐋𝐚𝐬𝐭 𝐛𝐮𝐭 𝐧𝐨𝐭 𝐥𝐞𝐚𝐬𝐭, 𝐩𝐥𝐞𝐚𝐬𝐞 𝐝𝐨 𝐧𝐨𝐭 𝐬𝐡𝐚𝐫𝐞 𝐚𝐧𝐲 𝐢𝐧𝐟𝐨𝐫𝐦𝐚𝐭𝐢𝐨𝐧 𝐚𝐛𝐨𝐮𝐭 𝐭𝐡𝐢𝐬 𝐬𝐭𝐮𝐝𝐲 𝐰𝐢𝐭𝐡 𝐚𝐧𝐲 𝐨𝐭𝐡𝐞𝐫𝐬. We will notify everyone when it is okay to do so after we finish the research project. (we will notify everyone when that is ready). Thank you! \n\n"""
    )
    
   
    name = {
        "title": "Please enter your name (first and last):",
        "questionItem": {
            "question": {
                "required": True,
                "textQuestion": {
                    "paragraph": True
                }
            }
        }
    }
    
    institution = {
        "title": "Please enter the full name of your institution:",
        "questionItem": {
            "question": {
                "required": True,
                "textQuestion": {
                    "paragraph": True
                }
            }
        }
    }
    
    email = {
        "title": "Please enter your email:",
        "questionItem": {
            "question": {
                "required": True,
                "textQuestion": {
                    "paragraph": True
                }
            }
        }
    }
    
    consent = {
    "title": "Consent: I have read the above information and have received answers to any questions I had. I consent to participate in the study.",
    "questionItem": {
        "question": {
            "required": True,
            "choiceQuestion": {
                "type": "RADIO",
                "options": [
                    {"value": "yes"},
                    {"value": "no"}
                ],
                "shuffle": False  # Optional: Shuffle the options
            }
        }
    }
    }
    
    GPT_use = {
    "title": "I confirm that I will not use ChatGPT, Claude, Gemini, or any other AI tools when writing my reviews.",
    "questionItem": {
        "question": {
            "required": True,
            "choiceQuestion": {
                "type": "RADIO",
                "options": [
                    {"value": "yes"},
                    {"value": "no"}
                ],
                "shuffle": False  # Optional: Shuffle the options
            }
        }
    }
    }
    
    expertise = {
    "title": "you will be reviewing an idea on: " + topic + " Before reviewing the idea, please indicate how familiar you are with the given topic on a scale of 1 - 5 (this is just for us to understand potential confounders):",
    "questionItem": {
        "question": {
            "required": True,
            "choiceQuestion": {
                "type": "RADIO",
                "options": [
                    {"value": "1 (you have never read about this topic before)"},
                    {"value": "2 (you have read at least one paper on this topic)"},
                    {"value": "3 (you have read multiple papers on this topic but have not published any paper on it)"},
                    {"value": "4 (you have co-authored at least one paper on this topic)"},
                    {"value": "5 (you have co-authored multiple papers on this topic or have published at least one first-author paper on this topic)"}
                ],
                "shuffle": False  # Optional: Shuffle the options
            }
        }
    }
    }
    
    reviewed_before = {
    "title": "Have you reviewed for major NLP or AI conferences before (e.g., *ACL, COLING, NeurIPS, ICLR, ICML, AAAI)?",
    "questionItem": {
        "question": {
            "required": True,
            "choiceQuestion": {
                "type": "RADIO",
                "options": [
                    {"value": "yes"},
                    {"value": "no"}
                ],
                "shuffle": False  # Optional: Shuffle the options
            }
        }
    }
    }
    
    
    novelty_mult_choice = {
    "title": "𝐍𝐨𝐯𝐞𝐥𝐭𝐲: Whether the idea is creative and different from existing works on the topic, and brings fresh insights. You are encouraged to search for related works online. You should consider all papers that appeared online prior to July 2024 as existing work when judging the novelty.",
    "questionItem": {
        "question": {
            "required": True,
            "choiceQuestion": {
                "type": "RADIO",
                "options": [
                    {"value": "1 (not novel at all - there are many existing ideas that are the same)"},
                    {"value": "2"},
                    {"value": "3 (mostly not novel - you can find very similar ideas)"},
                    {"value": "4"},
                    {"value": "5 (somewhat novel - there are differences from existing ideas but not enough to turn into a new paper)"},
                    {"value": "6 (reasonably novel - there are some notable differences from existing ideas and probably enough to turn into a new paper)"},
                    {"value": "7"},
                    {"value": "8 (clearly novel - major differences from all existing ideas)"},
                    {"value": "9"},
                    {"value": "10 (very novel - very different from all existing ideas in a very interesting and clever way)"}
                ],
                "shuffle": False  # Optional: Shuffle the options
            }
        }
    }
    }
    novelty_written_q = {
        "title": "Free-Text Rationale: Short justification for your score. If you give a low score, you should specify similar related works. (Your rationale should be at least 2-3 sentences.)",
        "questionItem": {
            "question": {
                "required": True,
                "textQuestion": {
                    "paragraph": True
                }
            }
        }
    }
    
    feasability_mult_choice = {
        "title": "𝐅𝐞𝐚𝐬𝐢𝐛𝐢𝐥𝐢𝐭𝐲: How feasible it is to implement and execute this idea as a research project? Specifically, how feasible the idea is for a typical CS PhD student to execute within 1-2 months of time. You can assume that we have abundant OpenAI / Anthropic API access, but limited GPU compute.",
    "questionItem": {
        "question": {
            "required": True,
            "choiceQuestion": {
                "type": "RADIO",
                "options": [
                    {"value": "1 (Impossible: the idea doesn't make sense or the proposed experiments are flawed and cannot be implemented)"},
                    {"value": "2"},
                    {"value": "3 (Very challenging: there are flaws in the proposed method or experiments, or the experiments require compute/human resources beyond any academic lab)"},
                    {"value": "4"},
                    {"value": "5 (Moderately feasible: It can probably be executed within the given time frame but would require careful planning, efficient use of APIs or some advanced computational strategies to overcome the limited GPU resources, and would require some modifications to the original proposal to make it work.)"},
                    {"value": "6 (Feasible: Can be executed within the given constraints with some reasonable planning.)"},
                    {"value": "7"},
                    {"value": "8 (Highly Feasible: Straightforward to implement the idea and run all the experiments.)"},
                    {"value": "9"},
                    {"value": "10 (Easy: The whole proposed project can be quickly executed within a few days without requiring advanced technical skills.)"}
                ],
                "shuffle": False  # Optional: Shuffle the options
            }
        }
        }
    }
    
    feasability_written = {
        "title": "Free-Text Rationale: Short justification for your score. If you give a low score, you should specify what parts are difficult to execute and why. (Your rationale should be at least 2-3 sentences.)",
        "questionItem": {
            "question": {
                "required": True,
                "textQuestion": {
                    "paragraph": True
                }
            }
        }
    }
    
    feasability2_mult_choice = {
        "title": "𝐄𝐱𝐩𝐞𝐜𝐭𝐞𝐝 𝐄𝐟𝐟𝐞𝐜𝐭𝐢𝐯𝐞𝐧𝐞𝐬𝐬: How likely the proposed idea is going to work well (e.g., better than existing baselines). ",
    "questionItem": {
        "question": {
            "required": True,
            "choiceQuestion": {
                "type": "RADIO",
                "options": [
                    {"value": "1 (Extremely Unlikely: The idea has major flaws and definitely won't work well.)"},
                    {"value": "2"},
                    {"value": "3 (Low Effectiveness: The idea might work in some special scenarios but you don't expect it to work in general.)"},
                    {"value": "4"},
                    {"value": "5 (Somewhat ineffective: There might be some chance that the proposed idea can work better than existing baselines but the improvement will be marginal or inconsistent.)"},
                    {"value": "6 (Somewhat effective: There is a decent chance that the proposed idea can beat existing baselines by moderate margins on a few benchmarks.)"},
                    {"value": "7"},
                    {"value": "8 (Probably Effective: The idea should offer some significant improvement over current methods on the relevant benchmarks.)"},
                    {"value": "9"},
                    {"value": "10 (Definitely Effective: You are very confident that the proposed idea will outperform existing methods by significant margins on many benchmarks.)"}
                ],
                "shuffle": False  # Optional: Shuffle the options
            }
        }
        }
    }
    
    feasability2_written = {
        "title": "Free-Text Rationale: Short justification for your score. (Your rationale should be at least 2-3 sentences.)",
        "questionItem": {
            "question": {
                "required": True,
                "textQuestion": {
                    "paragraph": True
                }
            }
        }
    }
    
    excitement_mult_choice = {
        "title": "𝐄𝐱𝐜𝐢𝐭𝐞𝐦𝐞𝐧𝐭: How exciting and impactful this idea would be if executed as a full project. Would the idea change the field and be very influential.",
    "questionItem": {
        "question": {
            "required": True,
            "choiceQuestion": {
                "type": "RADIO",
                "options": [
                    {"value": "1 (Poor: You cannot identify the contributions of this idea, or it's not interesting at all and you would fight to have it rejected at any major AI conference)"},
                    {"value": "2"},
                    {"value": "3 (Mediocre: this idea makes marginal contributions and is very incremental)"},
                    {"value": "4"},
                    {"value": "5 (Leaning negative: it has interesting bits but overall not exciting enough)"},
                    {"value": "6 (Learning positive: exciting enough to be accepted at a major AI conference, but still has some weaknesses or somewhat incremental)"},
                    {"value": "7"},
                    {"value": "8 (Exciting: would deepen the community's understanding or make major progress in this research direction)"},
                    {"value": "9"},
                    {"value": "10 (Transformative: would change the research field profoundly and worth a best paper award at major AI conferences)"}
                ],
                "shuffle": False  # Optional: Shuffle the options
            }
        }
        }
    }
    
    overall_mult = {
        "title": "Overall score:  Apart from the above, you should also give an overall score for the idea on a scale of 1 - 10 as defined below (Major AI conferences in the descriptions below refer to top-tier NLP/AI conferences such as *ACL, COLM, NeurIPS, ICLR, and ICML.):",
    "questionItem": {
        "question": {
            "required": True,
            "choiceQuestion": {
                "type": "RADIO",
                "options": [
                    {"value": "1 (Critically flawed, trivial, or wrong, would be a waste of students’ time to work on it)"},
                    {"value": "2 (Strong rejection for major AI conferences)"},
                    {"value": "3 (Clear rejection for major AI conferences)"},
                    {"value": "4 (Ok but not good enough, rejection for major AI conferences)"},
                    {"value": "5 (Decent idea but has some weaknesses or not exciting enough, marginally below the acceptance threshold of major AI conferences)"},
                    {"value": "6 (Marginally above the acceptance threshold of major AI conferences)"},
                    {"value": "7 (Good idea, would be accepted by major AI conferences)"},
                    {"value": "8 (Top 50% of all published ideas on this topic at major AI conferences, clear accept)"},
                    {"value": "9 (Top 15% of all published ideas on this topic at major AI conferences, strong accept)"},
                    {"value": "10 (Top 5% of all published ideas on this topic at major AI conferences, will be a seminal paper)"}
                ],
                "shuffle": False  # Optional: Shuffle the options
            }
        }
        }
    }
    
    overall_written = {
        "title": "You should also provide a rationale for your overall score (Your rationale should be at least 2-3 sentences.):",
        "questionItem": {
            "question": {
                "required": True,
                "textQuestion": {
                    "paragraph": True
                }
            }
        }
    }
    
    confidence_mult_choice = {
        "title": "Additionally, we ask for your confidence in your review on a scale of 1 to 5 defined as following:",
    "questionItem": {
        "question": {
            "required": True,
            "choiceQuestion": {
                "type": "RADIO",
                "options": [
                    {"value": "1 (Your evaluation is an educated guess)"},
                    {"value": "2 (You are willing to defend the evaluation, but it is quite likely that you did not understand central parts of the paper)"},
                    {"value": "3 (You are fairly confident that the evaluation is correct)"},
                    {"value": "4 (You are confident but not absolutely certain that the evaluation is correct)"},
                    {"value": "5 (You are absolutely certain that the evaluation is correct and very familiar with the relevant literature)"}
                ],
                "shuffle": False  # Optional: Shuffle the options
            }
        }
        }
    }
    
    time_spent_written = {
        "title": "How many minutes did you spend on this task?",
        "questionItem": {
            "question": {
                "required": True,
                "textQuestion": {
                    "paragraph": True
                }
            }
        }
    }
    
    
    new_form = {
        "info": {
            "title": "Research Idea Evaluation"
        }
    }
    
    form = forms_service.forms().create(body=new_form).execute()
    form_id = form['formId']
    
    update_body = {
        "requests": [
            
            {
                "updateFormInfo": {
                    "info": {
                        "description": instructions
                    },
                    "updateMask": "description"
                }
            }, 
            {
            "createItem": {
                "item": name,
                "location": {
                    "index": 0  # Adjust the index as needed
                }
            }
            },
            {
            "createItem": {
                "item": institution,
                "location": {
                    "index": 1  # Adjust the index as needed
                }
            }
            },
            {
            "createItem": {
                "item": email,
                "location": {
                    "index": 2  # Adjust the index as needed
                }
            }
            },
            {
            "createItem": {
                "item": consent,
                "location": {
                    "index": 3  # Adjust the index as needed
                }
            }
            },
            {
            "createItem": {
                "item": GPT_use,
                "location": {
                    "index": 4  # Adjust the index as needed
                }
            }
            },
            {
            "createItem": {
                "item": expertise,
                "location": {
                    "index": 5  # Adjust the index as needed
                }
            }
            },
            {
            "createItem": {
                "item": reviewed_before,
                "location": {
                    "index": 6  # Adjust the index as needed
                }
            }
            },
            {
            "createItem": {
                "item": {
                    "title": "Research Idea:",
                    "description": experiment_description + "\n Here is a link where you can view the idea in a separate text file: " + link,
                    "textItem": {}
                },
                "location": {
                    "index": 7  # Adjust the index as needed
                }
            }
            },
            {
            "createItem": {
                "item": novelty_mult_choice,
                "location": {
                    "index": 8  # Adjust the index as needed
                }
            }
            },
            {
                "createItem": {
                    "item": novelty_written_q,
                    "location": {
                        "index": 9  # Adjust the index as needed
                    }
                }
            },
            {
                "createItem": {
                    "item": feasability_mult_choice,
                    "location": {
                        "index": 10  # Adjust the index as needed
                    }
                }
            },
            {
                "createItem": {
                    "item": feasability_written,
                    "location": {
                        "index": 11  # Adjust the index as needed
                    }
                }
            },
             {
                "createItem": {
                    "item": feasability2_mult_choice,
                    "location": {
                        "index": 12  # Adjust the index as needed
                    }
                }
            },
            {
                "createItem": {
                    "item": feasability2_written,
                    "location": {
                        "index": 13 # Adjust the index as needed
                    }
                }
            },
            {
                "createItem": {
                    "item": excitement_mult_choice,
                    "location": {
                        "index": 14  # Adjust the index as needed
                    }
                }
            },
            {
                "createItem": {
                    "item": feasability2_written,
                    "location": {
                        "index": 15  # Adjust the index as needed
                    }
                }
            },
            {
                "createItem": {
                    "item": overall_mult,
                    "location": {
                        "index": 16  # Adjust the index as needed
                    }
                }
            },
            {
                "createItem": {
                    "item": overall_written,
                    "location": {
                        "index": 17  # Adjust the index as needed
                    }
                }
            },
            {
                "createItem": {
                    "item": confidence_mult_choice,
                    "location": {
                        "index": 18  # Adjust the index as needed
                    }
                }
            },
            {
                "createItem": {
                    "item": time_spent_written,
                    "location": {
                        "index": 19  # Adjust the index as needed
                    }
                }
            }
        ]
    }
    batch_update_response = forms_service.forms().batchUpdate(formId=form_id, body=update_body).execute()
    
    permission1 = {
        'type': 'user',
        'role': 'writer',
        'emailAddress': 'g24isha@gmail.com',  # Please set your email of Google account.
    }
    drive_service.permissions().create(fileId=form_id, body=permission1, sendNotificationEmail=False).execute()
    permission2 = {
        'type': 'user',
        'role': 'writer',
        'emailAddress': 'sichenglei1125@gmail.com',  # Please set your email of Google account.
    }
    drive_service.permissions().create(fileId=form_id, body=permission2, sendNotificationEmail=False).execute()
       
    form_url = f"https://docs.google.com/forms/d/{form_id}/edit"
    
       

    return form_url, form_id

def create_google_form_with_retry(description, topic, link):
    return execute_with_backoff(create_google_form, description,topic, link)
        
def update_cell_with_backoff(sheet, row, col, value):
    execute_with_backoff(sheet.update_cell, row, col, value)
    
def find_row(rows, title):
    row = 1
    for x in rows:
        for y in x:
            index = y.find('.')
            y = y [:index]
            if y.lower().strip() == title.lower():
                return row
        row += 1
    return 0
        
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

    for form_url, row in file_data:
        update_cell_with_backoff(sheet1, row, 7, form_url)

        
    print(f"Data appended to spreadsheet: {spreadsheet.url}")
   
def get_topic(name):
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
    RANGE_NAME = 'AllIdeas!C:C'
    result = service.spreadsheets().values().get(
        spreadsheetId=SPREADSHEET_ID,
        range=RANGE_NAME
    ).execute()
    values = result.get('values', [])
    print(name)
    row = find_row(values, name)
    if row == 0:
        return 0, "[no topic was returned]"
    sheet_name = 'AllIdeas'
    column = 'A'
    range_notation = f'{sheet_name}!{column}{row}'  
    result2 = service.spreadsheets().values().get(
                    spreadsheetId=SPREADSHEET_ID,
                    range=range_notation
                ).execute()
    values2 = result2.get('values', [])
    for i in values2:
        for z in i:
            index1 = z.find('#')
            z = z[:index1].strip()
            if z == "Bias":
                return row, "[Bias: novel prompting methods to reduce social biases and stereotypes of large language models]"
            if z == "Coding":
                return row, "[Coding: novel prompting methods for large language models to improve code generation]"
            if z == "Safety":
                return row, "[Safety: novel prompting methods to improve large language models' robustness against adversarial attacks or improve their security or privacy]"
            if z == "Multilingual":
                return row, "[Multilingual: novel prompting methods to improve large language models’ performance on multilingual tasks or low-resource languages and vernacular languages]"
            if z == "Factuality":
                return row, "[Factuality: novel prompting methods that can improve factuality and reduce hallucination of large language models]"
            if z == "Math":
                return row, "[Math: novel prompting methods for large language models to improve mathematical problem solving]"
            if z == "Uncertainty":
                return row, "[Uncertainty: novel prompting methods that can better quantify uncertainty or calibrate the confidence of large language models]"


FOLDER_ID = '1nnMYE2GHI8yvSAUEUx-dj2aAf_HMIbvM'

# List all files in the folder
results = drive_service.files().list(
    q=f"'{FOLDER_ID}' in parents",
    spaces='drive',
    fields='nextPageToken, files(id, name)').execute()
items = results.get('files', [])

x = 0

file_data = []
if not items:
    print('No files found.')
else:
    for item in items:
        # if x >= 1:
        #     break
        file_id = item['id']
        file_name = item['name']
        index = file_name.find('.txt')
        name = file_name[:index]
        row, topic = get_topic(name)
        if row == 0:
            print("UNUSED AI + HUMAN IDEAS: ", name)
            continue
        if not topic:
            topic = "[No topic was returned]"
        link, file_content = read_file_content_with_retry(file_id)
        form_url, form_id = create_google_form_with_retry(file_content, topic, link)
        file_data.append((form_url, row))
        print(f"Created form with ID: {form_id} from file: {file_name}")
        x += 1
        

create_spreadsheet(file_data)