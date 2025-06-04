import requests
import json
from django.conf import settings
import phonenumbers


def format_phone_number(phone):
    if phone.startswith("+98"):
        return "0" + phone[3:] 
    return phone

import logging
import requests
from django.conf import settings

logger = logging.getLogger(__name__)


def send_otp_sms(phone_number, otp):
    url = "https://intlsms.ferzz.ir/afg/send-message"
    # message = f"به نانزی خوش آمدید\nکد تایید شما: {otp}"
    payload = {
        "phone": str(format_phone_number(phone_number)),
        "code":otp,
        "token": settings.API_KEY_FERZZ,
    }

    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
    except requests.RequestException as e:

        logger.error(f"Request failed: {str(e)}")
        return None, f"Connection error: {str(e)}"

    if response.status_code == 200:
        data = response.json()
        otp_code = data.get("code")
        return otp_code, None
    else:

        logger.error(f"Error Response: {response.status_code} - {response.text}")
        return None, f"Status code {response.status_code}: {response.text}"


def reverse_geocode(lat, lng):
    url = f"https://api.neshan.org/v5/reverse?lat={lat}&lng={lng}"
    headers = {"Api-Key": settings.NESHAN_API}

    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        return None
