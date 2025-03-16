from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import *
from phonenumber_field.modelfields import PhoneNumberField

User = get_user_model()


class SendOTPSerializer(serializers.Serializer):
    phonenumber = serializers.CharField()

    def validate_phonenumber(self, value):
        return value


class LoginVerifyOTPSerializer(serializers.Serializer):
    phonenumber = serializers.CharField()
    otp = serializers.CharField(max_length=6)

    def validate(self, data):
        phonenumber = data.get("phonenumber")
        otp = data.get("otp")

        try:
            user=User.objects.get(phonenumber=phonenumber)
            otp_saved = Otp.objects.get(phonenumber=phonenumber)
            if not otp_saved.is_otp_valid():
                raise serializers.ValidationError("OTP expired, request a new one.")
            if otp_saved.otp != otp:
                raise serializers.ValidationError("Invalid OTP.")
        except User.DoesNotExist:
            raise serializers.ValidationError("User not found.")

        return data
