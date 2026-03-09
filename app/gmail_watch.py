import os
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]

creds = None

# Load existing token
if os.path.exists("token.json"):
    creds = Credentials.from_authorized_user_file("token.json", SCOPES)

# If token does not exist or expired → login once
if not creds or not creds.valid:
    flow = InstalledAppFlow.from_client_secrets_file(
        "credentials.json",
        SCOPES
    )

    creds = flow.run_local_server(port=0)

    # Save token for future use
    with open("token.json", "w") as token:
        token.write(creds.to_json())

# Build Gmail API client
service = build("gmail", "v1", credentials=creds)

request = {
    "topicName": "projects/meetloaf-hackathon/topics/gmail-events-topic"
}

response = service.users().watch(
    userId="me",
    body=request
).execute()

print(response)