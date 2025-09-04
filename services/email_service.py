import os
import base64
import os.path
from email.message import EmailMessage
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# Gmail API scope for sending emails
SCOPES = ['https://www.googleapis.com/auth/gmail.send']

def gmail_authenticate():
    creds = None
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
            creds = flow.run_local_server(port=0)
        with open("token.json", "w") as token:
            token.write(creds.to_json())
    return build("gmail", "v1", credentials=creds)


class EmailService:
    sender_email = ''

    def __init__(self, sender_email):
        self.sender_email = sender_email

    def send(self, subject, body, recipients):
        message = EmailMessage()
        message.set_content(body)
        message["To"] = recipients
        message["From"] = self.sender_email
        message["Subject"] = subject

        encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()

        send_message = {"raw": encoded_message}
        sent = gmail_authenticate().users().messages().send(userId="me", body=send_message).execute()
        print(f'Message Id: {sent["id"]}')
