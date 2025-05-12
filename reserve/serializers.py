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
    user = UserSerializer(read_only=True)
    delivery=DeliverySlotSerializer(read_only=True)
    delivery_id = serializers.IntegerField(write_only=True)
    location_id=serializers.IntegerField(write_only=True)
    total_price = serializers.SerializerMethodField()
    next_delivery_date = serializers.ReadOnlyField()
    location = LocationSerializer(read_only=True)

    class Meta:
        model = BreadReservation
        fields = [
            "location",
            "user",
            "delivery",
            "period",
            "active",
            "auto_pay",
            "total_price",
            "next_delivery_date",
    
        ]
        read_only_fields = [
            "text",
            "user",
        ]  

    def to_representation(self, instance):

        representation = super().to_representation(instance)
        if "text" not in representation:
            representation["text"] = "".join(
                secrets.choice(string.ascii_uppercase + string.digits)
                for _ in range(10)
            )
        representation["next_delivery_date"] = instance.next_delivery_date()

        return representation

class ReservationProductSerializer(serializers.ModelSerializer):
    product = ProductCartSerializer()
    reserve = ReservationSerializer()
    class Meta:
        model = ReserveItem
        fields = ["reserve", "product", "quantity"]


class OrderReservationSerializer(serializers.Serializer):
    is_paid=serializers.BooleanField()
