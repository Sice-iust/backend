from django.db import models
from django.utils import timezone
from rest_framework import serializers
from django.contrib.auth import get_user_model
from product.models import *
from cart.models import *
from .models import *
from product.serializers import *
from users.models import Location
import secrets
import string
from rest_framework import serializers
import pytz
from django.utils import timezone
from datetime import datetime


User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model=User
        fields=['username','phonenumber']

class UserDiscountSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = ["phonenumber"]


class DiscountOrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = DiscountCart
        fields = ["text"]


class LocationSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    address = serializers.CharField()

    class Meta:
        model = Location
        fields = ["user", "address", "name", "reciver", "phonenumber"]


class DeliverySlotSerializer(serializers.ModelSerializer):

    class Meta:
        model = DeliverySlots
        fields = "__all__"


class DeliverySlotsByDaySerializer(serializers.Serializer):
    delivery_date = serializers.DateField()
    slots = DeliverySlotSerializer(many=True)


class FinalizeOrderSerializer(serializers.Serializer):
    location = LocationSerializer()
    deliver_time = serializers.IntegerField()
    discription = serializers.CharField(required=False, allow_blank=True)
    total_price = serializers.DecimalField(max_digits=10, decimal_places=2)
    profit = serializers.DecimalField(max_digits=10, decimal_places=2)
    total_payment = serializers.DecimalField(max_digits=10, decimal_places=2)
    discount_text = serializers.CharField(required=False, allow_blank=True)
    payment_status = serializers.CharField(default="unpaid")


class MyOrderSerializer(serializers.ModelSerializer):
    delivery=DeliverySlotSerializer()
    location = LocationSerializer()
    class Meta:
        model=Order
        fields = [
            "id",
            "location",
            "delivery",
            "total_price",
            "status",
            "profit",
            "discription",
            "delivered_at",
        ]


class MyOrderItemSerializer(serializers.ModelSerializer):
    order=MyOrderSerializer()
    product=ProductCartSerializer()

    class Meta:
        model = OrderItem
        fields = ["order", "product", "quantity", "product_discount"]


class DiscountCartSerializer(serializers.ModelSerializer):
    phonenumber = serializers.CharField(write_only=True)
    product_name = serializers.CharField(write_only=True)
    product = ProductDiscountSerializer(read_only=True)
    class Meta:
        model = DiscountCart
        fields = [
            "id",
            "phonenumber",
            "product_name",
            "product",
            "text",
            "percentage",
            "max_discount",
            "max_use",
            "first_time",
            "expired_time",
            "payment_without_discount",
        ]
        read_only_fields = ["text"] 

    def create(self, validated_data):
        phone = validated_data.pop("phonenumber")
        product_name = validated_data.pop("product_name")

        try:
            user = User.objects.get(phonenumber=phone)
        except User.DoesNotExist:
            raise serializers.ValidationError(
                {"phonenumber": "No user with this phonenumber exists."}
            )

        try:
            product = Product.objects.get(name=product_name)
        except Product.DoesNotExist:
            raise serializers.ValidationError(
                {"product_name": "No product with this name exists."}
            )

        random_text = "".join(
            secrets.choice(string.ascii_uppercase + string.digits) for _ in range(10)
        )

        validated_data["user"] = user
        validated_data["product"] = product
        validated_data["text"] = random_text

        return super().create(validated_data)

    def to_representation(self, instance):

        representation = super().to_representation(instance)

        if "text" not in representation:

            representation["text"] = "".join(
                secrets.choice(string.ascii_uppercase + string.digits)
                for _ in range(10)
            )

        return representation

class OrderInvoiceSerializer(serializers.ModelSerializer):
    product = ProductCartSerializer()
    class Meta:
        model=OrderItem
        fields = ["product", "quantity"]
