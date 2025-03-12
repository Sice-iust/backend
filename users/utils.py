import requests
import json

import phonenumbers


def format_phone_number(phone):
    if phone.startswith("+98"):
        return "0" + phone[3:] 
    return phone


def send_otp_sms(phone_number, otp):
    url = "https://gateway.ghasedak.me/rest/api/v1/WebService/SendOtpWithParams"
    formatted_phone = format_phone_number(phone_number)
    payload = json.dumps({
    "date": 0,
    "receptors": [
        {
        "mobile": str(formatted_phone) ,
        "clientReferenceId":"1"
        }
    ],
    "templateName": "Ghasedak",
    "param1": otp,
    "isVoice": False,
    "udh": False
    })
    headers = {
        "Content-Type": "application/json",
        "ApiKey": "4b646babf144a075eb91ed03b9e90bce07e4fa161fbea872067639ef51f21844hCfrEKXWzzPHk25C",
    }

    response = requests.request("POST", url, headers=headers, data=payload)

    print(response.text)
