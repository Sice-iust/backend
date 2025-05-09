from django.db import models
from django.utils import timezone
from rest_framework import serializers
# from django.contrib.auth import get_user_model
from .models import *


class WalletTransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model=WalletTransaction
        fields=['wallet','status','type','value','description']
        read_only_fields = ['wallet', 'status']
        extra_kwargs = {
            'description': {'required': False},
        }
    def create(self, validated_data):
        validated_data['wallet'] = self.context.get('wallet')
        validated_data['status'] = self.context.get('status')

        if not validated_data['wallet'] or not validated_data['status']:
            raise serializers.ValidationError("wallet and status must be provided in context.")
        return super().create(validated_data)
    
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