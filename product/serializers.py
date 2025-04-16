from .models import *
from rest_framework import serializers
from django.contrib.auth import get_user_model
User = get_user_model()
from drf_spectacular.utils import extend_schema_field

from rest_framework import serializers

class SubcategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Subcategory
        fields = ['subcategory']

class ProductSerializer(serializers.ModelSerializer):
    photo = serializers.SerializerMethodField("get_image")
    discounted_price = serializers.SerializerMethodField('get_new_price')
    subcategories = SubcategorySerializer(many=True,required=False)
    class Meta:
        model = Product
        fields = ["id", "category", "name", "price", "description",'stock',
        "photo", "average_rate", 'discount', 'discounted_price','subcategories']

    def get_image(self, obj):
        if obj.photo and hasattr(obj.photo, "url"):
            return self.context["request"].build_absolute_uri(obj.photo.url)
        return None

    def get_new_price(self, obj):
        if obj.discount is not None and obj.discount > 0 and obj.price is not None:
            return obj.price - (obj.price * obj.discount / 100)
        return obj.price 
    
    def create(self, validated_data):
        subcategories_data = validated_data.pop('subcategories')
        product = Product.objects.create(**validated_data)
        existing_subcategories = set()
        for subcategory in subcategories_data:
            subcategory_value = subcategory['subcategory']
            if subcategory_value not in existing_subcategories:
                Subcategory.objects.create(product=product, subcategory=subcategory_value)
                existing_subcategories.add(subcategory_value)
        return product
class ProductRateSerializer(serializers.ModelSerializer):
    class Meta:
        model=Product
        fields = ["id","name"]


class RateSerializer(serializers.ModelSerializer):
    product=ProductRateSerializer()

    class Meta:
        model=Rate
        fields = ["product", "rate"]


class ProductCartSerializer(serializers.ModelSerializer):
    photo = serializers.SerializerMethodField("get_image")
    class Meta:
        model = Product
        fields = ["id", "name", "price", "photo"]

    def get_image(self, obj):
        if obj.photo and hasattr(obj.photo, "url"):
            return self.context["request"].build_absolute_uri(obj.photo.url)
        return None


class ProductDiscountSerializer(serializers.ModelSerializer):

    class Meta:
        model = Product
        fields = ['name']
