from django.shortcuts import render
from .models import *
from .serializers import *
from django.contrib.auth import get_user_model
User = get_user_model()
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated,AllowAny
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from drf_spectacular.utils import extend_schema, OpenApiExample
from payment.views import ZarinpalPayment
from payment.models import ZarinpalTransaction
from django.conf import settings
from django.shortcuts import redirect

CALL_BACKURL = "https://nanziback.liara.run/user/wallet-verify/" #'http://127.0.0.1:8000/user/wallet-verify'#
ZARINPAL_THRESH = 10000
HOME_PAGE = "https://nanzi-amber.vercel.app/"
class WalletView(APIView):
    user_wallet_serializer_class = UserWalletSerializer
    transaction_serializer_class = WalletTransactionSerializer
    permission_classes  = [IsAuthenticated]

    def get(self, request):
        user = request.user
        wallet, _ = UserWallet.objects.get_or_create(user=user)
        return Response(
            {"balance": wallet.balance},
            status=201
        )

    @extend_schema(
    request=WalletTransactionSerializer,
    responses={200: openapi.Response(description="Transaction was successful")},
    examples=[
        OpenApiExample(
            "Sample Credit",
            value={
                "type": 1,  # Credit
                "value": "100.00",
                "description": "Credit"
            },
            request_only=True,
        ),
         OpenApiExample(
            "Sample Deposit",
            value={
                "type": 2,  # Deposit
                "value": "100.00",
                "description": "Deposit"
            },
            request_only=True,
        )
    ]
    )

    def post(self,request):
        user = request.user
        wallet, _ = UserWallet.objects.get_or_create(user=user)
        serializer = self.transaction_serializer_class(
            data=request.data,
            context={"wallet": wallet, "status": WalletTransaction.Status.PENDING}
        )

        if not serializer.is_valid():
            return Response({"message": "Something went wrong", "errors": serializer.errors}, status=400)
        if serializer.validated_data['type'] != WalletTransaction.Type.Credit:
            wallet = UserWallet.objects.get(user=user)
            tx = WalletTransaction.objects.create(
                wallet=wallet, value=serializer.validated_data['value'],description=serializer.validated_data['description']
                ,type=WalletTransaction.Type.Debit)
            #some logic
            tx.status = WalletTransaction.Status.SUCCESS
            try:
                wallet.apply_transaction(tx)
                return Response({"message": "Debit completed"}, status=200)
            except ValidationError as e:
                return Response({"message": "something went wrong", 'error':str(e)}, status=400)
           
        if serializer.validated_data['value'] < ZARINPAL_THRESH:
            return Response({"message": "Too small transaction"}, status=400)
        payment_class = ZarinpalPayment(callback_url=CALL_BACKURL)
        res = payment_class.request(user, int(serializer.validated_data['value']),serializer.validated_data['description'],settings.MERCHANT_ID)
        return res
class WalletVerifyView(APIView):
    def get(self, request):
        authority = request.GET.get('Authority')
        status = request.GET.get('Status')

        if not authority:
            return redirect(HOME_PAGE)
        if not status:
            return redirect(HOME_PAGE)
        elif status != 'OK':
            return redirect(HOME_PAGE)
        else: 
            payment_class = ZarinpalPayment(callback_url=CALL_BACKURL)
            res = payment_class.verify(status,authority,settings.MERCHANT_ID,None)
            tx = ZarinpalTransaction.objects.get(authority=authority)

            if res.status_code == 200:
                if res.data.get('status') == 'completed':
                    wallet = UserWallet.objects.get(user=tx.user)
                    tx_wallet = WalletTransaction.objects.create(
                        wallet=wallet, description="Zarinpal payment", status=WalletTransaction.Status.SUCCESS,
                        type=WalletTransaction.Type.Credit, value=tx.amount)
                    wallet = UserWallet.objects.get(user=tx.user)
                    wallet.apply_transaction(tx_wallet)
                    return redirect(HOME_PAGE+"/ProfilePage")
                else:
                    return redirect(HOME_PAGE)


        return redirect(HOME_PAGE)


