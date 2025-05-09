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

    photo = serializers.ImageField(write_only=True, required=False)
    photo_url = serializers.SerializerMethodField()
    discounted_price = serializers.SerializerMethodField()
    subcategories = SubcategorySerializer(many=True, required=False)

    class Meta:
        model = Product
        fields = [
            "id",
            "category",
            "name",
            "price",
            "description",
            "stock",
            "box_type",
            "box_color",
            "color",
            "photo",  
            "photo_url", 
            "average_rate",
            "discount",
            "discounted_price",
            "subcategories",
        ]

    def get_photo_url(self, obj):
        request = self.context.get("request")
        if obj.photo and hasattr(obj.photo, "url") and request:
            return request.build_absolute_uri(obj.photo.url)
        return None

    def get_discounted_price(self, obj):
        if obj.discount and obj.price:
            return obj.price - (obj.price * obj.discount / 100)
        return obj.price

    def create(self, validated_data):
        subcategories_data = validated_data.pop("subcategories", [])
        product = Product.objects.create(**validated_data)
        existing_subcategories = set()
        for subcategory in subcategories_data:
            subcategory_value = subcategory["subcategory"]
            if subcategory_value not in existing_subcategories:
                Subcategory.objects.create(
                    product=product, subcategory=subcategory_value
                )
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


class SummerizedProductCartSerializer(serializers.ModelSerializer):
    photo = serializers.SerializerMethodField("get_image")
    class Meta:
        model = Product
        fields = [
            "id",
            "photo", "name",
            "price",
            "discount",
            "stock",
            "box_type",
            "box_color",
            "color",
        ]

    def validate_price(self, value):
        return value if value is not None else 0

    def get_image(self, obj):
        if obj.photo and hasattr(obj.photo, "url"):
            return self.context["request"].build_absolute_uri(obj.photo.url)
        return None


class ProductDiscountSerializer(serializers.ModelSerializer):

    class Meta:
        model = Product
        fields = ['name']
class ProductCommentSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductComment
        fields = ['comment','suggested']

    def create(self, validated_data):
        validated_data['user'] = self.context.get('user')
        validated_data['product'] = self.context.get('product')

        if not validated_data['user'] or not validated_data['product']:
            raise serializers.ValidationError("User and product must be provided in context.")
        return super().create(validated_data)
    
    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['user_name'] = instance.user.username
        data['suggested_label'] = instance.suggested
        data['posted_at'] = instance.posted_at
        return data
