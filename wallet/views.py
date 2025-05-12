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
from drf_spectacular.utils import extend_schema


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
    responses={200: openapi.Response(description="Transaction was successful")}
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
        tx = serializer.save()
        # some function to handle transaction
        if True: # change later
            tx.status = WalletTransaction.Status.SUCCESS
            try:
                wallet.apply_transaction(tx)
                return Response({"message": "Transaction was successful"})
            except ValidationError as e:
                return Response({"message": "Something went wrong", "errors": e.message}, status=400)
                
        else:
            tx.status = WalletTransaction.Status.FAILED
            return Response({"message": "Something went wrong", "errors": "transaction failed"}, status=400)


