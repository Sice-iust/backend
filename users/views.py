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
from .utils import send_otp_sms, reverse_geocode
from rest_framework.permissions import IsAuthenticated,AllowAny
from django.utils.timezone import now
from datetime import timedelta, datetime
import random
from django.utils import timezone
from rest_framework.parsers import MultiPartParser, FormParser
from order.models import DiscountCart
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework.parsers import MultiPartParser, FormParser

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
    permission_classes = [AllowAny]
    serializer_class=ProfileSerializer
    def get(self, request):
        if request.user.is_authenticated:
            user = request.user
            seria = self.serializer_class(user, context={"request": request})
            return Response(seria.data)
        return Response({"message":"no login"})

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
    serializer_class = LogOutSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=400)

        try:
            token = RefreshToken(serializer.validated_data["refresh_token"])
            token.blacklist()
            return Response({"message": "Logged out successfully."}, status=200)
        except TokenError:
            return Response({"error": "Invalid or expired token."}, status=400)


class LocationView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = LocationSerializer

    def get(self, request):
        user = request.user
        locations = Location.objects.filter(user=user).all() 
        if not locations.exists():
            return Response(
                {"error": "You have not submitted any locations yet."}, status=404
            )

        serializer = self.serializer_class(locations, many=True)
        return Response(serializer.data)

    def post(self, request):
        user = request.user

        name = request.data.get("name")
        reciver = request.data.get("reciver")
        phonenumber = request.data.get("phonenumber")
        address=request.data.get('address')
        Location.objects.filter(user=user, is_choose=True).update(is_choose=False)
        location = Location.objects.create(
            user=user,
            name=name,
            reciver=reciver,
            phonenumber=phonenumber,
            address=address,
            is_choose=True
        )


        return Response(LocationSerializer(location).data, status=201)


class SingleLocationView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = LocationSerializer


    def put(self, request, id):
        user = request.user
        try:
            location = Location.objects.get(id=id, user=user)
        except Location.DoesNotExist:
            return Response(
                {"error": "Location not found or not owned by user."},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = self.serializer_class(location, data=request.data, partial=True)
        if serializer.is_valid():
            if request.data.get("is_choose") is not None or True:
                Location.objects.filter(user=user).exclude(id=location.id).update(
                    is_choose=False
                )

                serializer.save(is_choose=True)
            else:
                serializer.save()
            return Response(serializer.data)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, id):
        user = request.user
        try:
            location = Location.objects.get(id=id, user=user)
        except Location.DoesNotExist:
            return Response(
                {"error": "Location not found or not owned by user."},
                status=status.HTTP_404_NOT_FOUND,
            )
        location.delete()
        return Response(
            {"message": "Location deleted successfully."},
            status=status.HTTP_204_NO_CONTENT,
        )


class NeshanLocationView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="lng", description="Longitude", required=True, type=float
            ),
            OpenApiParameter(
                name="lat", description="Latitude", required=True, type=float
            ),
        ]
    )
    def get(self, request):
        lng = request.query_params.get("lng")
        lat = request.query_params.get("lat")

        if not lng or not lat:
            return Response({"error": "lng and lat are required"}, status=400)

        try:
            lng = float(lng)
            lat = float(lat)
        except ValueError:
            return Response({"error": "lng and lat must be floats"}, status=400)

        try:
            data = reverse_geocode(lat, lng)
        except Exception as e:
            return Response({"error": f"Neshan API failed: {str(e)}"}, status=500)

        if not data:
            return Response({"error": "Neshan API returned no data"}, status=500)

        return Response(data)


class ChooseLocationView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request, id):
        user = request.user
        try:
            location = Location.objects.get(id=id, user=user)
        except Location.DoesNotExist:
            return Response(
                {"error": "Location not found or not owned by user."},
                status=status.HTTP_404_NOT_FOUND,
            )

        Location.objects.filter(user=user).exclude(id=location.id).update(
            is_choose=False
        )

        location.is_choose = True
        location.save()

        return Response(
            {"success": "Location successfully chosen."},
            status=status.HTTP_200_OK,
        )
