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

class SignUPVerifyOTPSerializer(serializers.Serializer):
    phonenumber = serializers.CharField()
    username = serializers.CharField()
    otp = serializers.CharField(max_length=6)
