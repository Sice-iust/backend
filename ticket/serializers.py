from django.contrib.auth import get_user_model
from rest_framework import serializers
from .models import Ticket
from order.serializers import UserSerializer, MyOrderSerializer
from django.shortcuts import get_object_or_404
from order.models import Order

User = get_user_model()


class TicketSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    order = MyOrderSerializer(read_only=True)
    order_id = serializers.IntegerField(write_only=True, required=False)

    class Meta:
        model = Ticket
        fields = [
            "id",
            "user",
            "title",
            "description",
            "priority",
            "category",
            "created_at",
            "updated_at",
            "order",
            "order_id",
            "admin_check",
            "is_close",
            "admin_answer",
        ]
        read_only_fields = ["admin_check", "admin_answer"]


class AdminTicketSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    order = MyOrderSerializer(read_only=True)
    order_id = serializers.IntegerField(write_only=True, required=False)

    class Meta:
        model = Ticket
        fields = [
            "id",
            "user",
            "title",
            "description",
            "priority",
            "category",
            "created_at",
            "updated_at",
            "order",
            "order_id",
            "admin_check",
            "is_close",
            "admin_answer",
        ]


class PatchAdminSerializer(serializers.Serializer):
    admin_answer = serializers.CharField()
    admin_check = serializers.BooleanField()


class PatchUserSerializer(serializers.Serializer):
    is_close = serializers.BooleanField()
