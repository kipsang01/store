import africastalking

from store import settings


def send_sms_notification(phone_number, message):
    """Send an SMS notification using Africa's Talking API.

    Args:
        phone_number (str): The phone number to send the SMS to.
        message (str): The message to send.

    Returns:
        dict: The response from the Africa's Talking API.
    """
    username = settings.AFRICAS_TALKING_USERNAME
    api_key = settings.AFRICAS_TALKING_API_KEY
    sender_id = settings.AFRICAS_TALKING_SENDER_ID
    africastalking.initialize(username=username, api_key=api_key)
    sms = africastalking.SMS

    try:
        response = sms.send(message, [phone_number], sender_id=sender_id)
        return response
    except Exception as e:
       raise e