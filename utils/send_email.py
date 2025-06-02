from smtplib import SMTPException

from django.core.mail import send_mail, BadHeaderError

from store import settings


def send_admin_email(subject, email_body):
    """Send an email notification to the admin when a new order is placed.
    Args:
        subject (str): The subject of the email.
        email_body (str): The body of the email.
    """

    try:
        send_mail(
            subject,
            email_body,
            settings.DEFAULT_FROM_EMAIL,
            [settings.ADMIN_EMAIL],
            fail_silently=False,
        )
    except BadHeaderError:
        raise ValueError("Invalid header found")
    except SMTPException as e:
        raise ValueError(f"SMTP error occurred: {e}")