from __future__ import print_function

import base64
from email.message import EmailMessage
from typing import Iterator



import google.auth
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from assistance.domain.entities import AttLog

from assistance.domain.repo import AttLogRepo
from assistance.infra.mails_google.settings import MailsSettings

def gmail_send_message(from_email: str, to: str, subject: str, content: str):
    """Create and send an email message
    Print the returned  message id
    Returns: Message object, including message id

    Load pre-authorized user credentials from the environment.
    TODO(developer) - See https://developers.google.com/identity
    for guides on implementing OAuth2 for the application.
    """
    creds, _ = google.auth.default()

    try:
        service = build('gmail', 'v1', credentials=creds)
        message = EmailMessage()

        message.set_content(content)

        message['To'] = to
        message['From'] = from_email
        message['Subject'] = subject

        # encoded message
        encoded_message = base64.urlsafe_b64encode(message.as_bytes()) \
            .decode()

        create_message = {
            'raw': encoded_message
        }
        # pylint: disable=E1101
        send_message = (service.users().messages().send
                        (userId="me", body=create_message).execute())
        print(F'Message Id: {send_message["id"]}')
    except HttpError as error:
        print(F'An error occurred: {error}')
        send_message = None
    return send_message


class MailRepo(AttLogRepo):

    def __init__(self, settings: MailsSettings):
        self._settings = settings

    def save(self, logs: Iterator[AttLog]):
        from_email = self._settings.from_email
        message = self._settings.message
        for log in logs:
            to = f"{log.dni}@{self._settings.google_domain}"
            subject = f"{self._settings.subject_prefix} {str(log.date)} {str(log.time)}"
            gmail_send_message(from_email=from_email, to=to, subject=subject, message=message)