from .models import *
from rest_framework import serializers
from django.contrib.auth import get_user_model
User = get_user_model()

from rest_framework import serializers

class ProductSerializer(serializers.ModelSerializer):
    photo = serializers.SerializerMethodField("get_image")
    dicounted_price = serializers.SerializerMethodField('get_new_price')  \

    class Meta:
        model = Product
        fields = ["id", "category", "name", "price", "description",
        "photo", "average_rate", 'discount', 'dicounted_price']

    def get_image(self, obj):
        if obj.photo and hasattr(obj.photo, "url"):
            return self.context["request"].build_absolute_uri(obj.photo.url)
        return None

    def get_new_price(self, obj):
        if obj.discount is not None and obj.discount > 0 and obj.price is not None:
            return obj.price - (obj.price * obj.discount / 100)
        return obj.price 

class ProductRateSerializer(serializers.ModelSerializer):
    class Meta:
        model=Product
        fields = ["id","name"]


class RateSerializer(serializers.ModelSerializer):
    product=ProductRateSerializer()

    class Meta:
        model=Rate
        fields = ["product", "rate"]


# class DiscountSerializer(serializers.ModelSerializer):
#     Product=ProductRateSerializer()

#     class Meta:
#         model = Rate
#         fields = ["product", "percentage"]
