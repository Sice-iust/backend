import requests
import json
from django.conf import settings
import phonenumbers


def format_phone_number(phone):
    if phone.startswith("+98"):
        return "0" + phone[3:] 
    return phone




def send_otp_sms(phone_number):
    url = "https://api.ferzz.ir/services/call/call/"
    payload = {
        "destination": str(format_phone_number(phone_number)),
        "token": settings.API_KEY_FERZZ,
    }

    try:
        response = requests.post(url, json=payload)
    except requests.RequestException as e:
        return None, f"Connection error: {str(e)}"

    if response.status_code == 200:
        data = response.json()
        otp_code = data.get("code")
        return otp_code, None
    else:
        return None, f"Status code {response.status_code}: {response.text}"


def reverse_geocode(lat, lng):
    url = f"https://api.neshan.org/v5/reverse?lat={lat}&lng={lng}"
    headers = {"Api-Key": settings.NESHAN_API}

    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        return None
