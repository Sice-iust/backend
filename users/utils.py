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

    payload = json.dumps({
    "receptors": [
        {
        "mobile": str(format_phone_number(phone_number)),
        "clientReferenceId": "1"
        }
    ],
    "templateName": "Ghasedak",
    "inputs": [
        {
        "param": "Code",
        "value": str(otp)
        }
    ],
    "udh": True
    })
    headers = {
        "Content-Type": "application/json",
        "ApiKey": "4b646babf144a075eb91ed03b9e90bce07e4fa161fbea872067639ef51f21844hCfrEKXWzzPHk25C",
    }

    response = requests.request("POST", url, headers=headers, data=payload)

    print(response.text)
