from rest_framework import serializers
from .models import BreadReservation
from product.serializers import ProductDiscountSerializer
from order.serializers import UserSerializer
import secrets
import string
from users.serializers import LocationSerializer
from product.models import Product
from order.models import DeliverySlots
from django.contrib.auth import get_user_model
from users.models import Location
from decimal import Decimal

User = get_user_model()
class DeliverySlotSerializer(serializers.ModelSerializer):
    class Meta:
        model = DeliverySlots
        fields = ["start_time", "end_time", "delivery_date", "shipping_fee"]


class ReservationSerializer(serializers.ModelSerializer):
    product_id = serializers.IntegerField(write_only=True)
    phonenumber = serializers.CharField(write_only=True)
    product = ProductDiscountSerializer(read_only=True)
    user = UserSerializer(read_only=True)
    delivery=DeliverySlotSerializer(read_only=True)
    delivery_id=serializers.IntegerField(write_only=True)
    total_price = serializers.SerializerMethodField()
    next_delivery_date = serializers.ReadOnlyField()
    location = LocationSerializer(read_only=True)
    location_id = serializers.IntegerField(write_only=True, required=False)

    class Meta:
        model = BreadReservation
        fields = [
            "product",
            "delivery_id",
            "location",
            "location_id",
            "user",
            "quantity",
            "delivery",
            "period",
            "active",
            "auto_pay",
            "total_price",
            "next_delivery_date",
            "product_id",
            "phonenumber",
        ]
        read_only_fields = [
            "text",
            "user",
            "product",
        ]  

    def get_total_price(self, obj):
        try:
            base_price = obj.product.price
            total_items =  obj.quantity
            discount = obj.product.discount or 0
            discount_rate = Decimal(1) - (Decimal(discount) / Decimal(100))
            discounted_price = base_price * discount_rate
            return discounted_price * total_items
        except:
            return 0

    def create(self, validated_data):
        location_id = validated_data.pop("location_id", None)
        phone = validated_data.pop("phonenumber")
        product_id = validated_data.pop("product_id")
        delivery_id=validated_data.pop('delivery_id')
        try:
            user = User.objects.get(phonenumber=phone)
        except User.DoesNotExist:
            raise serializers.ValidationError(
                {"phonenumber": "No user with this phone number exists."}
            )

        try:
            product = Product.objects.get(id=product_id)
        except Product.DoesNotExist:
            raise serializers.ValidationError(
                {"product_name": "No product with this name exists."}
            )
        try:
            delivery = DeliverySlots.objects.get(id=delivery_id)
        except DeliverySlots.DoesNotExist:
            raise serializers.ValidationError(
                {"product_name": "No Delivery with this name exists."}
            )
        validated_data["user"] = user
        validated_data["product"] = product
        validated_data["delivery"] = delivery
        if location_id:
            try:
                location = Location.objects.get(id=location_id)
                validated_data["location"] = location
            except Location.DoesNotExist:
                raise serializers.ValidationError({"location_id": "Invalid location."})
        return super().create(validated_data)

    def to_representation(self, instance):

        representation = super().to_representation(instance)
        if "text" not in representation:
            representation["text"] = "".join(
                secrets.choice(string.ascii_uppercase + string.digits)
                for _ in range(10)
            )
        representation["next_delivery_date"] = instance.next_delivery_date()

        return representation

class OrderReservationSerializer(serializers.Serializer):
    is_paid=serializers.BooleanField()
