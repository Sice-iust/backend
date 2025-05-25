import requests
from rest_framework.response import Response
from rest_framework import status
from .models import ZarinpalTransaction
from .payments import PaymentGateway

class ZarinpalPayment(PaymentGateway):
    def __init__(self, callback_url):
        super().__init__(
            name="Zarinpal",
            description="Zarinpal Payment Gateway",
            callback_url=callback_url,
            request_url="https://sandbox.zarinpal.com/pg/v4/payment/request.json",
            verify_url="https://sandbox.zarinpal.com/pg/v4/payment/verify.json",
        )

    def redirect_url(self):
        return f"https://sandbox.zarinpal.com/pg/StartPay/"

    def request(self, user, amount, description, merchant_id):
        data = {
            "merchant_id": merchant_id,
            "amount": amount,
            "callback_url": self.callback_url,
            "description": description,
        }

        headers = {"accept": "application/json", "content-type": "application/json"}

        try:
            print(self.request_url)
            response = requests.post(self.request_url, json=data, headers=headers)
            print("Response Status:", response.status_code)
            print("Response Data:", response.json())
            response.raise_for_status()  
        except requests.RequestException as e:
            return Response(
                {"detail": "Connection to payment gateway failed.", "error": str(e)},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        response_data = response.json()
        if (
            response.status_code == 200
            and response_data.get("data", {}).get("code") == 100
        ):
            authority = response_data["data"]["authority"]
            try:
                ZarinpalTransaction.objects.create(
                    user=user, authority=authority, amount=amount, status="pending"
                )
            except Exception as e:
           
                return Response(
                    {"detail": "Failed to save transaction.", "error": str(e)},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )
            redirect_url = f"{self.redirect_url()}{authority}"
            return Response({"payment_url": redirect_url},status=200)

        return Response(response_data, status=status.HTTP_400_BAD_REQUEST)

    def verify(self, status_query, authority, merchant_id, amount):
        try:
            transaction = ZarinpalTransaction.objects.get(authority=authority)
        except ZarinpalTransaction.DoesNotExist:
            return Response({"detail": "Transaction not found."}, status=404)

        if status_query != "OK":
            transaction.status = "failed"
            transaction.save()
            return Response(
                {
                    "detail": "Transaction canceled or failed.",
                    "status": transaction.status,
                },
                status=400,
            )

        data = {
            "merchant_id": merchant_id,
            "amount": int(transaction.amount),
            "authority": authority,
        }

        headers = {"accept": "application/json", "content-type": "application/json"}

        try:
            response = requests.post(self.verify_url, json=data, headers=headers)
            response.raise_for_status()
        except requests.RequestException as e:
            return Response(
                {"detail": "Verification request failed.", "error": str(e)},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        if response.status_code == 200:
            data = response.json().get("data", {})
            code = data.get("code")
            if code==101:
                return Response({"message":"you submit later.","status": transaction.status,})
            if code== 100:
                transaction.status = "completed"
                transaction.save()
                return Response(
                    {
                        "message": "Payment verified.",
                        "ref_id": data.get("ref_id"),
                        "card_pan": data.get("card_pan"),
                        "status": transaction.status,
                    }
                )

        transaction.status = "failed"
        transaction.save()
        return Response(
            {
                "detail": response.json(),
                "status": transaction.status,
                "redirect_url": "/payment/result?status=failed",
            },
            status=400,
        )
