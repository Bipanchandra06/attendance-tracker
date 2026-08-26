import base64
from email.mime.text import MIMEText

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.core.mail import send_mail as django_send_mail


def send_email(subject, body, recipients):
    """Send through Gmail API in production and the console backend locally."""
    if not recipients:
        return

    configured = all((
        settings.GMAIL_CLIENT_ID,
        settings.GMAIL_CLIENT_SECRET,
        settings.GMAIL_REFRESH_TOKEN,
        settings.GMAIL_SENDER_EMAIL,
    ))
    if not configured:
        if settings.DEBUG:
            django_send_mail(subject, body, settings.DEFAULT_FROM_EMAIL or None, recipients)
            return
        raise ImproperlyConfigured('Gmail API credentials are not configured.')

    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build

    credentials = Credentials(
        token=None,
        refresh_token=settings.GMAIL_REFRESH_TOKEN,
        token_uri='https://oauth2.googleapis.com/token',
        client_id=settings.GMAIL_CLIENT_ID,
        client_secret=settings.GMAIL_CLIENT_SECRET,
        scopes=['https://www.googleapis.com/auth/gmail.send'],
    )
    credentials.refresh(Request())

    message = MIMEText(body, 'plain', 'utf-8')
    message['To'] = ', '.join(recipients)
    message['From'] = settings.GMAIL_SENDER_EMAIL
    message['Subject'] = subject
    encoded = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')

    service = build('gmail', 'v1', credentials=credentials, cache_discovery=False)
    service.users().messages().send(userId='me', body={'raw': encoded}).execute()
