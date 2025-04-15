from django.db import models
from django.utils import timezone
from rest_framework import serializers
from django.contrib.auth import get_user_model
from product.models import *
from cart.models import *
from .models import *
from product.serializers import *
import secrets
import string

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


class MyOrderSerializer(serializers.ModelSerializer):
    delivery_day = serializers.SerializerMethodField()
    user=UserSerializer()
    delivery_clock = serializers.SerializerMethodField()
    class Meta:
        model=Order
        fields = [
            "id",
            "distination",
            "user",
            "delivery_time",
            "delivery_day",
            "delivery_clock",
            "total_price",
            "status",
            'shipping_fee',
        ]

    def get_delivery_day(self, obj):
        return obj.get_jalali_delivery_day()

    def get_delivery_clock(self, obj):
        return obj.get_jalali_delivery_time()


class MyOrderItemSerializer(serializers.ModelSerializer):
    order=MyOrderSerializer()
    product=ProductCartSerializer()

    class Meta:
        model = OrderItem
        fields = ["order", "product", "quantity", "product_discount"]


class FinalizeOrderSerializer(serializers.Serializer):
    distination=serializers.CharField()
    deliver_time=serializers.DateTimeField()
    discription = serializers.CharField(
        required=False,
        allow_blank=True,
    )
    shipping_fee = serializers.DecimalField(max_digits=10, decimal_places=2)
    total_price = serializers.DecimalField(max_digits=10, decimal_places=2)
    discount = serializers.DecimalField(max_digits=10, decimal_places=2)
    total_payment = serializers.DecimalField(max_digits=10, decimal_places=2)

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
