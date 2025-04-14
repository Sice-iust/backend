from django.contrib.auth import get_user_model
from rest_framework import serializers
from product.models import Product
from product.serializers import ProductCartSerializer
from .models import CartItem

User = get_user_model()


from django.contrib.auth import get_user_model
from rest_framework import serializers
from product.models import Product
from product.serializers import ProductCartSerializer
from .models import CartItem

User = get_user_model()


class CartSerializer(serializers.ModelSerializer):
    product = ProductCartSerializer()
    price = serializers.SerializerMethodField(method_name="get_price")
    total_price = serializers.SerializerMethodField(method_name="get_total_price")
    total_discount = serializers.SerializerMethodField(method_name="get_total_discount")
    total_actual_price = serializers.SerializerMethodField(
        method_name="get_total_actual_price"
    )
    stock=serializers.SerializerMethodField(method_name='get_stock')
    class Meta:
        model = CartItem
        fields = [
            "product",
            "quantity",
            'stock',
            "price",
            "total_discount",
            "total_price",
            "total_actual_price",
        ]

    def get_stock(self,obj):
        
        return obj.product.stock
    
    def get_price(self, obj):
   
        return obj.product.price * obj.quantity

    def get_total_price(self, obj):
        
        price = obj.product.price * obj.quantity
        return price

    def get_total_actual_price(self, obj):
      
        price_before_discount = obj.product.price * obj.quantity
        discount = (obj.product.price * obj.product.discount / 100) * obj.quantity
        return price_before_discount - discount

    def get_total_discount(self, obj):
      
        return (obj.product.price * obj.product.discount / 100) * obj.quantity


class CRUDCartSerializer(serializers.Serializer):
    quantity=serializers.IntegerField()


class CartDiscountSerializer(serializers.Serializer):
    final_price = serializers.FloatField()
    discount = serializers.FloatField()
