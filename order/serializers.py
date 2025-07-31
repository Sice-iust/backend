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
from cart.serializers import SummerizedCartSerializer
User = get_user_model()
import jdatetime
from rest_framework import serializers
from .models import DeliverySlots

PERSIAN_WEEKDAYS = ["شنبه", "یک‌شنبه", "دوشنبه", "سه‌شنبه", "چهارشنبه", "پنج‌شنبه", "جمعه"]


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["username", "phonenumber"]


class UserDiscountSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = ["phonenumber"]


class LocationSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    address = serializers.CharField()

    class Meta:
        model = Location
        fields = ["user", "address", "name", "home_floor", "home_unit", "home_plaque"]


class DeliverySlotSerializer(serializers.ModelSerializer):
    day_name = serializers.SerializerMethodField()

    class Meta:
        model = DeliverySlots
        fields = "__all__"

    def get_day_name(self, obj):
        if obj.delivery_date:
            jdate = jdatetime.date.fromgregorian(date=obj.delivery_date)
            return PERSIAN_WEEKDAYS[jdate.weekday()]
        return None


class DeliverySlotsByDaySerializer(serializers.Serializer):
    delivery_date = serializers.DateField()
    slots = DeliverySlotSerializer(many=True)


def cart_info(request):
    user = request.user
    cart_items = CartItem.objects.filter(user=user)
    if not cart_items:
        return {}
    serializer = SummerizedCartSerializer(
        cart_items, many=True, context={"request": request}
    )
    total_price = 0
    total_discount = 0

    for item in cart_items:
        price = item.product.price or 0
        discount = item.product.discount or 0
        quantity = item.quantity

        total_price += price * quantity
        total_discount += (price * discount / 100) * quantity 

    total_actual_price = total_price - total_discount
    if total_actual_price<0:
        total_actual_price=0

    shipping_fee = -1
    delivery_cart = DeliveryCart.objects.filter(user=user).last()
    if (delivery_cart and delivery_cart.delivery.delivery_date >= timezone.now().date() and 
            delivery_cart.delivery.current_fill<delivery_cart.delivery.max_orders):
        shipping_fee = delivery_cart.delivery.shipping_fee or 0

    counts= CartItem.objects.filter(user=user).count()
    return {
            "cart_items": serializer.data,
            "total_discount": total_discount,
            "total_actual_price": total_actual_price,
            "shipping_fee":shipping_fee,
            "total_actual_price_with_shipp":total_actual_price+shipping_fee,
            "counts":counts,
        }

class FinalizeOrderSerializer(serializers.Serializer):
    location_id = serializers.IntegerField(write_only=True)
    deliver_time = serializers.IntegerField()
    description = serializers.CharField(required=False, allow_blank=True)
    total_price = serializers.DecimalField(max_digits=10, decimal_places=2)
    profit = serializers.DecimalField(max_digits=10, decimal_places=2)
    total_payment = serializers.DecimalField(max_digits=10, decimal_places=2)
    discount_text = serializers.CharField(required=False, allow_blank=True)
    payment_status = serializers.CharField(default="unpaid")
    reciver = serializers.CharField()
    reciver_phone = serializers.CharField()
    def validate(self, attrs):
        request = self.context.get("request")
        if request:
            cart = cart_info(request)
            if cart:
                attrs['profit'] = cart['total_discount']
                attrs['total_price'] = cart['total_actual_price_with_shipp']
                attrs['total_payment'] = attrs['total_price'] - attrs['profit']
                attrs['payment_status'] = 'unpaid'
            else:
                raise serializers.ValidationError("Cart is empty.")
        return attrs

class MyOrderSerializer(serializers.ModelSerializer):
    delivery = DeliverySlotSerializer()
    location = LocationSerializer()

    class Meta:
        model = Order
        fields = [
            "id",
            "location",
            "delivery",
            "total_price",
            "status",
            "profit",
            "description",
            "delivered_at",
            "reciver",
            "reciver_phone",
            "is_admin_canceled",
            "admin_reason",
            "is_archive",
        ]


class MyOrderItemSerializer(serializers.ModelSerializer):
    order = MyOrderSerializer()
    product = ProductCartSerializer()

    class Meta:
        model = OrderItem
        fields = ["order", "product", "quantity", "product_discount"]


class OrderInvoiceSerializer(serializers.ModelSerializer):
    product = ProductCartSerializer()

    class Meta:
        model = OrderItem
        fields = ["product", "quantity"]


class AdminCancelSerializer(serializers.Serializer):
    order_id = serializers.IntegerField()
    reason = serializers.CharField()


class AdminArchiveSerializer(serializers.Serializer):
    order_id = serializers.IntegerField()


class StatusSerializer(serializers.Serializer):
    order_id = serializers.IntegerField()
    status = serializers.IntegerField()


class OrderIdSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = ["id"]
