from django.db import models
from django.utils import timezone
from rest_framework import serializers
# from django.contrib.auth import get_user_model
from .models import *


class WalletTransactionSerializer(serializers.ModelSerializer):
    description = serializers.TextField(required=False, allow_blank=True)
    class Meta:
        model=WalletTransaction
        fields=['wallet','status','type','value','description']
        
    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['transaction_id'] = instance.transaction_id
        data['at'] = instance.at
        return data
    
class UserWalletSerializer(serializers.ModelSerializer):
    class Meta:
        model=UserWallet
        fields=['user']

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['balance'] = instance.balance
        data['created_on'] = instance.created_on
        data['updated_at'] = instance.updated_at
        return data