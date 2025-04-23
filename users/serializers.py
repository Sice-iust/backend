from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import *
from phonenumber_field.modelfields import PhoneNumberField
from drf_spectacular.utils import extend_schema_field
from order.serializers import UserSerializer
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

class LogOutSerializer(serializers.Serializer):
    refresh_token=serializers.CharField()

class ProfileSerializer(serializers.ModelSerializer):
    profile_photo = serializers.SerializerMethodField()
    class Meta:
        model=User
        fields=['username','profile_photo']
    def get_profile_photo(self, obj):
        request = self.context.get("request")
        if obj.profile_photo and hasattr(obj.profile_photo, "url"):
            return request.build_absolute_uri(obj.profile_photo.url)
        return request.build_absolute_uri("/media/profiles/Default_pfp.jpg")

from drf_spectacular.utils import (
    extend_schema_field,
    OpenApiTypes,
    OpenApiParameter
) 

class UpdateProfileSerializer(serializers.ModelSerializer):

    profile_photo = serializers.ImageField(required=False)

    class Meta:
        model = User
        fields = ["username", "profile_photo"]

    def update(self, instance, validated_data):
        profile_photo = validated_data.pop("profile_photo", None)
        if profile_photo:
            instance.profile_photo = profile_photo
        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()
        return instance

class LocationSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    class Meta:
        model=Location
        fields = ["id","user", "address", "name", "reciver","phonenumber"]