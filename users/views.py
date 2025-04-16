from django.shortcuts import render
from .models import *
from .serializers import *
from rest_framework_simplejwt.tokens import RefreshToken, TokenError
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
from datetime import timedelta, datetime
import random
from django.utils import timezone
from rest_framework.parsers import MultiPartParser, FormParser
from order.models import DiscountCart
class SendOTPView(APIView):
    serializer_class = SendOTPSerializer
    def post(self, request):
        serializer = SendOTPSerializer(data=request.data)
        if serializer.is_valid():
            phone = serializer.validated_data["phonenumber"]
            user = User.objects.filter(phonenumber=phone).first()

            ten_minutes_ago = now() - timedelta(minutes=10)
            recent_otps = Otp.objects.filter(
                phonenumber=phone, otp_created_at__gte=ten_minutes_ago
            )
            otp_count = recent_otps.count()
            if otp_count >= 3:
                return Response(
                    {"message": "You can only request 3 OTPs every 10 minutes."}
                )

            otp = Otp.objects.create(phonenumber=phone)
            otp = otp.generate_otp()

            send_otp_sms(phone, otp)
            return Response(
                {
                
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
            user = User.objects.filter(phonenumber=phone).last()
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

class SignUpVerifyOTPView(APIView):
    serializer_class = SignUPVerifyOTPSerializer
    def post(self,request):
        serializer = SignUPVerifyOTPSerializer(data=request.data)
        if serializer.is_valid():
            phone = serializer.validated_data["phonenumber"]
            user = User.objects.filter(phonenumber=phone).last()
            if user:
                return Response({"message":"this phone number is already registered."})
            otp_saved = Otp.objects.filter(phonenumber=phone).last()
            if not otp_saved:
                return Response({"message":"OTP is used or expired."})
            if not otp_saved.is_otp_valid():
                return Response({"message":"OTP expired, request a new one."})
            if otp_saved.otp != serializer.validated_data["otp"]:
                return Response("Invalid OTP.")
            User.objects.create(
                phonenumber=phone, username=serializer.validated_data["username"]
            )
            Otp.objects.filter(phonenumber=phone).delete()
            user = User.objects.filter(phonenumber=phone).first()
            login(request, user)
            refresh = RefreshToken.for_user(user)
            access_token = refresh.access_token
            DiscountCart.objects.create(user=user,text='Welcome',percentage=25,max_discount=80,max_use=1,first_time=False)
            return Response(
                {
                    "message": "SignUp successful",
                    "access_token": str(access_token),
                    "refresh_token": str(refresh),
                },
                status=status.HTTP_200_OK,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ProfileView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class=ProfileSerializer
    def get(self, request):
        user = request.user
        seria = self.serializer_class(user, context={"request": request})
        return Response(seria.data)

class UpdateProfileView(APIView):
    parser_classes = [MultiPartParser, FormParser]
    permission_classes = [IsAuthenticated]
    serializer_class = UpdateProfileSerializer

    def put(self, request):
        user = request.user
        serializer = self.serializer_class(
            user, data=request.data, partial=True, context={"request": request}
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=400)


class LogOutView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class=LogOutSerializer
    
    def post(self, request):
        refresh_token = self.serializer_class(data=request.data)
        if not refresh_token:
            return Response({"error": "Refresh token required."}, status=400)

        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response({"message": "Logged out successfully."}, status=200)
        except TokenError:
            return Response({"error": "Invalid or expired token."}, status=400)
