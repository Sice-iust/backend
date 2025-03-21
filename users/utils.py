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
