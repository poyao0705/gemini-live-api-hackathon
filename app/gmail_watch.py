# gmail_watch.py

from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]

def start_gmail_watch():

    flow = InstalledAppFlow.from_client_secrets_file(
        "credentials.json",
        SCOPES
    )

    creds = flow.run_local_server(port=0)

    service = build("gmail", "v1", credentials=creds)

    request = {
        "topicName": "projects/meetloaf-hackathon/topics/gmail-events-topic"
    }

    response = service.users().watch(
        userId="me",
        body=request
    ).execute()

    print("Watch started:", response)

    return response