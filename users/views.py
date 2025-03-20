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
from django.utils.timezone import now

class SendOTPView(APIView):
    serializer_class = SendOTPSerializer
    def post(self, request):
        serializer = SendOTPSerializer(data=request.data)
        if serializer.is_valid():
            phone = serializer.validated_data["phonenumber"]
            user = User.objects.filter(phonenumber=phone).first()
            otp_obj, created = Otp.objects.get_or_create(phonenumber=phone)
            otp = otp_obj.generate_otp()
            # print(otp)
            send_otp_sms(phone, otp)
            return Response(
                {
                    # "otp":otp,
                    "message": "OTP sent",
                    "is_registered": bool(user),
                },
                status=status.HTTP_200_OK,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LoginVerifyOTPView(APIView):
    serializer_class = LoginVerifyOTPSerializer
    def post(self, request):
        serializer = LoginVerifyOTPSerializer(data=request.data)
        if serializer.is_valid():
            phone = serializer.validated_data["phonenumber"]
            user = User.objects.get(phonenumber=phone)
            if not user:
                return Response({"message":"you are not registered."})
            otp_saved = Otp.objects.filter(phonenumber=phone).last()
            if not otp_saved:
                return Response({"message":"OTP is used or expired."})
            if not otp_saved.is_otp_valid():
                return Response({"message":"OTP expired, request a new one."})
            if otp_saved.otp != serializer.validated_data["otp"]:
                return Response("Invalid OTP.")
            login(request, user)
            refresh = RefreshToken.for_user(user)
            access_token = refresh.access_token
            Otp.objects.filter(phonenumber=phone).delete()
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
