import os
from typing import List, Optional
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build, Resource
from google.oauth2.credentials import Credentials
from email import message_from_bytes
import base64
import re

from email.message import Message
from inbox.provider.generic import InboxProvider

class GmailProvider(InboxProvider):
    def __init__(self, credentials_path: str = 'credentials.json', token_path: str = 'token.json', scopes: List[str] = ['https://www.googleapis.com/auth/gmail.modify']) -> None:
        self.credentials_path: str = credentials_path
        self.token_path: str = token_path
        self.scopes: List[str] = scopes
        self._service: Optional[Resource] = None
        self.history_id: Optional[str] = None  # Used to track the last synced state

    def getService(self) -> Resource:
        if self._service is None:
            self._service = self.authenticate()
        return self._service

    def authenticate(self) -> Resource:
        creds: Optional[Credentials] = None
        if os.path.exists(self.token_path):
            creds = Credentials.from_authorized_user_file(self.token_path, self.scopes)
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials_path, self.scopes)
                creds = flow.run_local_server(port=0)
            with open(self.token_path, 'w') as token:
                token.write(creds.to_json())

        service: Resource = build('gmail', 'v1', credentials=creds)
        return service

    def _convert_to_email_message(self, raw_message_data: str, gmail_message_id: str) -> Message:
        email_data = base64.urlsafe_b64decode(raw_message_data.encode('ASCII'))
        email_msg = message_from_bytes(email_data)
        email_msg['gmail_message_id'] = gmail_message_id
        return email_msg

    def sync_inbox(self, full_sync: bool = False) -> List[Message]:
        email_messages: List[Message] = []
        service: Resource = self.getService()
        max_results: int = 20

        if full_sync or self.history_id is None:
            results = service.users().messages().list(userId='me', maxResults=max_results).execute()
            print(results)
            messages = results.get('messages', [])
            if messages:
                
                for msg in reversed(messages):
                    message = service.users().messages().get(userId='me', id=msg['id'], format='raw').execute()
                    self.history_id = message['historyId']
                    email_msg = self._convert_to_email_message(message['raw'],  msg['id'])
                    email_messages.append(email_msg)
        else:
            results = service.users().history().list(userId='me', startHistoryId=self.history_id, maxResults=max_results).execute()
            print(results)
            self.history_id = results['historyId']
            changes = results.get('history', [])
            if changes:
                for change in changes:
                    if 'messagesAdded' in change:
                        for msg in reversed(change['messagesAdded']):
                            message = service.users().messages().get(userId='me', id=msg['message']['id'], format='raw').execute()
                            email_msg = self._convert_to_email_message(message['raw'], msg['message']['id'])
                            email_messages.append(email_msg)
        return email_messages
    def create_label(self, label_name: str) -> None:
        service = self.getService()
        existing_labels = service.users().labels().list(userId='me').execute().get('labels', [])
        for label in existing_labels:
            if label['name'] == label_name:
                return  # Return existing label if found
        label_body = {'name': label_name, 'labelListVisibility': 'labelShow', 'messageListVisibility': 'show'}
        service.users().labels().create(userId='me', body=label_body).execute()
        return

    def create_folder(self, folder_name: str) -> None:
        return self.create_label(folder_name)  # Reuse create_label since folders are labels in Gmail API

    def label_message(self, email_message: Message, label_ids: List[str]) -> None:
        if 'gmail_message_id' not in email_message:
            raise ValueError("email_message must contain a 'gmail_message_id' header")
        service = self.getService()
        current_labels = service.users().messages().get(userId='me', id=email_message['gmail_message_id'], format='metadata', metadataHeaders=['labels']).execute().get('labelIds', [])
        new_label_ids = [label_id for label_id in label_ids if label_id not in current_labels]  # Filter out already applied labels
        if not new_label_ids:  # If no new labels to add, return current state to maintain idempotency
            return
        body = {'addLabelIds': new_label_ids}
        service.users().messages().modify(userId='me', id=email_message['gmail_message_id'], body=body).execute()
        return

    def move_message_to_folder(self, email_message: Message, folder_id: str) -> None:
        if 'gmail_message_id' not in email_message:
            raise ValueError("email_message must contain a 'gmail_message_id' header")
        service = self.getService()
        current_labels = service.users().messages().get(userId='me', id=email_message['gmail_message_id'], format='metadata', metadataHeaders=['labels']).execute().get('labelIds', [])
        if 'INBOX' not in current_labels and folder_id in current_labels:  # Check if message is already moved
            return  # Return current state to maintain idempotency
        body = {'addLabelIds': [folder_id], 'removeLabelIds': ['INBOX']}
        service.users().messages().modify(userId='me', id=email_message['gmail_message_id'], body=body).execute()
        return
    
    def has_emailed_before(self, email: str) -> bool:
        # Extract email address from within angle brackets
        match = re.search(r'<(.+?)>', email)
        if match:
            email_address = match.group(1)
        else:
            # If no angle brackets are found, assume the whole string is the email address
            email_address = email

        service = self.getService()
        query = f'to:{email_address} in:sent'
        response = service.users().messages().list(userId='me', q=query, maxResults=1).execute()
        messages = response.get('messages', [])
        return len(messages) > 0

    def get_message_labels(self, email_message: Message) -> List[str]:
        if 'gmail_message_id' not in email_message:
            raise ValueError("email_message must contain a 'gmail_message_id' header")
        service = self.getService()
        labels_info = service.users().messages().get(userId='me', id=email_message['gmail_message_id'], format='metadata', metadataHeaders=['labels']).execute()
        return labels_info.get('labelIds', [])


    def archive_message(self, email_message: Message) -> None:
        if 'gmail_message_id' not in email_message:
            raise ValueError("email_message must contain a 'gmail_message_id' header")
        service = self.getService()
        body = {'removeLabelIds': ['INBOX']}
        service.users().messages().modify(userId='me', id=email_message['gmail_message_id'], body=body).execute()
        return
