from django.conf import settings
from django.core.mail import send_mail as django_send_mail


def send_email(subject, body, recipients):
    """Send through Gmail SMTP in production and the console backend locally."""
    if not recipients:
        return

    django_send_mail(subject, body, settings.DEFAULT_FROM_EMAIL or None, recipients)
