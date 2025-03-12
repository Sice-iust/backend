from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import *
from phonenumber_field.modelfields import PhoneNumberField

User = get_user_model()


class SendOTPSerializer(serializers.Serializer):
    phonenumber = serializers.CharField()

    def validate_phonenumber(self, value):
        if not User.objects.filter(phonenumber=value).exists():
            raise serializers.ValidationError("Phone number not registered.")
        return value


class VerifyOTPSerializer(serializers.Serializer):
    phonenumber = serializers.CharField()
    otp = serializers.CharField(max_length=6)

    def validate(self, data):
        phonenumber = data.get("phonenumber")
        otp = data.get("otp")

        try:
            user = User.objects.get(phonenumber=phonenumber)
            if not user.is_otp_valid():
                raise serializers.ValidationError("OTP expired, request a new one.")
            if user.otp != otp:
                raise serializers.ValidationError("Invalid OTP.")
        except User.DoesNotExist:
            raise serializers.ValidationError("User not found.")

        return data
