from django.shortcuts import render
from .models import *
from .serializers import *
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model
User = get_user_model()
from django.contrib.auth import login,authenticate
from rest_framework.authtoken.models import Token
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .utils import send_otp_sms
from rest_framework.permissions import IsAuthenticated

class SendOTPView(APIView):
    serializer_class = SendOTPSerializer
    def post(self, request):
        serializer = SendOTPSerializer(data=request.data)
        if serializer.is_valid():
            phone = serializer.validated_data["phonenumber"]
            user = User.objects.get(phonenumber=phone)
            user.generate_otp()  
            print(user.otp)
            # send_otp_sms(phone, user.otp)

            return Response({"message": "OTP sent"}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class VerifyOTPView(APIView):
    serializer_class = VerifyOTPSerializer
    def post(self, request):
        serializer = VerifyOTPSerializer(data=request.data)
        if serializer.is_valid():
            phone = serializer.validated_data["phonenumber"]
            user = User.objects.get(phonenumber=phone)
            login(request, user)
            refresh = RefreshToken.for_user(user)
            access_token = refresh.access_token
            return Response(
                {
                    "message": "Login successful",
                    "access_token": str(access_token),
                    "refresh_token": str(refresh),
                },
                status=status.HTTP_200_OK,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        return Response({"username": user.username})
