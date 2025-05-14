from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings
from .serializers import *
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.urls import reverse
import requests
from .models import ZarinpalTransaction


class ZarinpalPaymentRequestView(APIView):
    serializer_class = ZarinPallSerializer
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        user = request.user
        merchant_id = settings.MERCHANT_ID
        callback_url = request.build_absolute_uri(reverse("payment-verify"))

        if serializer.is_valid():
            amount = serializer.validated_data[
                "amount"
            ]  
            description = serializer.validated_data.get("description", "")

            data = {
                "merchant_id": merchant_id,
                "amount": amount,
                "callback_url": callback_url,
                "description": description,
            }

            headers = {"accept": "application/json", "content-type": "application/json"}
            response = requests.post(
                "https://sandbox.zarinpal.com/pg/v4/payment/request.json",
                json=data,
                headers=headers,
            )

            if (
                response.status_code == 200
                and response.json().get("data", {}).get("code") == 100
            ):
                authority = response.json()["data"]["authority"]
                ZarinpalTransaction.objects.create(
                    user=request.user,
                    authority=authority,
                    amount=serializer.validated_data["amount"],  
                    status="pending"
                )
                redirect_url = f"https://sandbox.zarinpal.com/pg/StartPay/{authority}"
                return Response({"payment_url": redirect_url})
            else:
                return Response(response.json(), status=status.HTTP_400_BAD_REQUEST)

        return Response(
            "You should provide correct data.", status=status.HTTP_400_BAD_REQUEST
        )

class ZarinpalPaymentVerifyView(APIView):
    def get(self, request):
        status_query = request.GET.get("Status")
        authority = request.GET.get("Authority")
        try:
            transaction = ZarinpalTransaction.objects.get(authority=authority)
        except ZarinpalTransaction.DoesNotExist:
            return Response(
                {"detail": "Transaction not found."},
                status=status.HTTP_404_NOT_FOUND,
            )
        amount=transaction.amount

        if status_query != "OK":
            transaction.status = "failed"
            transaction.save()
            return Response(
                {"detail": "Transaction canceled or failed."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        data = {
            "merchant_id": settings.MERCHANT_ID,
            "amount": int(amount),
            "authority": authority,
        }

        headers = {"accept": "application/json", "content-type": "application/json"}
        response = requests.post(
            "https://sandbox.zarinpal.com/pg/v4/payment/verify.json",
            json=data,
            headers=headers,
        )

        verify_data = response.json().get("data", {})
        code = verify_data.get("code")

        if code == 100 or code == 101:
            transaction.status = "completed"
            transaction.save()

            return Response(
                {
                    "message": "Payment verified.",
                    "ref_id": verify_data.get("ref_id"),
                    "card_pan": verify_data.get("card_pan"),
                    "status":transaction.status,
                }
            )
        else:
            transaction.status = "failed"
            transaction.save()

            return Response(
                {"detail": response.json(), "status": transaction.status},
                status=status.HTTP_400_BAD_REQUEST,
            )
