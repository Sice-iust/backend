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

    @swagger_auto_schema(
        operation_summary="Transaction request",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=["user", "amount"],
            properties={
                'value': openapi.Schema(type=openapi.TYPE_NUMBER, format='decimal', description='Transaction amount'),
                'type': openapi.Schema(type=openapi.TYPE_NUMBER, format='integer', description='Credit or Debit'),
                'description': openapi.Schema(type=openapi.TYPE_STRING, description='Optional description'),
            }
        ),
        responses={200: openapi.Response(description="Transaction processed")}
    )
    def post(self,request):
        user = request.user
        wallet, _ = UserWallet.objects.get_or_create(user=user)
        self.transaction_serializer_class(data=request.data,user=user,wallet=wallet)




