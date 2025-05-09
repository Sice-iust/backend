from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.core.exceptions import ValidationError
from decimal import Decimal
from utils import create_short_uuid4

User = get_user_model()
TRANSACTION_ID_LENGTH = 12

class UserWallet(models.Model):
    user = models.ForeignKey(User, unique=True, on_delete=models.PROTECT, related_name="user_wallet")
    balance = models.DecimalField(default=0,max_digits=12,decimal_places=2)
    created_on = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                check=models.Q(balance__gte=0),
                name="valid_balance",
            )
        ]

    def apply_transaction(self, transaction):
        if transaction.status != WalletTransaction.Status.SUCCESS or transaction.wallet!=self:
            raise ValidationError("Not a valid transaction for this wallet")  

        if transaction.type == WalletTransaction.Type.Credit:
            self.balance += Decimal(transaction.value)
        elif transaction.type == WalletTransaction.Type.Debit:
            if self.balance < transaction.value:
                raise ValidationError("Insufficient balance for transaction.")
            self.balance -= Decimal(transaction.value)
        self.save()

    def __str__(self):
        return f"{self.user} has {self.balance} at {self.updated_at}"
    

class WalletTransaction(models.Model):
    class Status(models.IntegerChoices):
        SUCCESS = 1, 'Success'
        PENDING = 2, 'Pending'
        FAILED = 3, 'Failed'

    class Type(models.IntegerChoices):
        Credit = 1, 'Credit' 
        Debit = 2, 'Debit' 

    wallet = models.ForeignKey(UserWallet, on_delete=models.PROTECT, related_name='wallet_transactions')
    transaction_id = models.CharField(default=create_short_uuid4(TRANSACTION_ID_LENGTH), editable=False, unique=True)
    description = models.TextField(blank=True)
    status = models.PositiveSmallIntegerField(choices=Status.choices, default=Status.PENDING)
    type = models.PositiveSmallIntegerField(choices=Type.choices)
    at = models.DateTimeField(default=timezone.now)
    value = models.DecimalField(max_digits=12,decimal_places=2)

    class Meta:
        constraints = [
            models.CheckConstraint(
                check=models.Q(value__gte=0),
                name="valid_value",
            )
        ]
    def __str__(self):
        return f"{self.wallet} {self.get_type_display()} {self.value} at {self.at} - status:{self.get_status_display()}"
