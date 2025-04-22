from rest_framework import serializers
from .models import BreadReservation
from product.serializers import ProductDiscountSerializer
from order.serializers import UserSerializer
import secrets
import string
from users.serializers import LocationSerializer

class ReservationSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(write_only=True)
    phonenumber = serializers.CharField(write_only=True)
    product = ProductDiscountSerializer(read_only=True)
    user = UserSerializer(read_only=True)
    total_price = serializers.SerializerMethodField()
    next_delivery_date = serializers.ReadOnlyField()
    location=LocationSerializer()
    class Meta:
        model = BreadReservation
        fields = [
            "product",
            "location",
            "user",
            "quantity",
            "period",
            "start_date",
            "active",
            "auto_pay",
            "total_price",
            "next_delivery_date",
            "product_name",  
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
            discounted_price = base_price * (1 - discount / 100)
            return round(discounted_price * total_items, 2)
        except:
            return 0

    def create(self, validated_data):
        phone = validated_data.pop("phonenumber")
        product_name = validated_data.pop("product_name")
        try:
            user = User.objects.get(phonenumber=phone)
        except User.DoesNotExist:
            raise serializers.ValidationError(
                {"phonenumber": "No user with this phone number exists."}
            )

        try:
            product = Product.objects.get(name=product_name)
        except Product.DoesNotExist:
            raise serializers.ValidationError(
                {"product_name": "No product with this name exists."}
            )

        validated_data["user"] = user
        validated_data["product"] = product

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
