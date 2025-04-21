import requests
import json
from django.conf import settings
import phonenumbers


def format_phone_number(phone):
    if phone.startswith("+98"):
        return "0" + phone[3:] 
    return phone


def send_otp_sms(phone_number, otp):
    url = "https://gateway.ghasedak.me/rest/api/v1/WebService/SendOtpSMS"

    payload = json.dumps(
        {
            "receptors": [
                {
                    "mobile": str(format_phone_number(phone_number)),
                    "clientReferenceId": "1",
                }
            ],
            "templateName": "nanzi",
            "inputs": [{"param": "Code", "value": str(otp)}],
            "udh": True,
        }
    )
    headers = {
        "Content-Type": "application/json",
        "ApiKey": settings.API_KEY,
    }

    response = requests.request("POST", url, headers=headers, data=payload)

    print(response.text)


def reverse_geocode(lat, lng):
    url = f"https://api.neshan.org/v5/reverse?lat={lat}&lng={lng}"
    headers = {"Api-Key": settings.NESHAN_API}

    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        return None
