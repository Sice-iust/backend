from django.db import models
from django.utils import timezone
from django.contrib.auth import get_user_model
from product.models import *
from cart.models import *
import jdatetime  
from django.utils import timezone
from datetime import timedelta
from users.models import Location

User = get_user_model()


def default_expired_time():
    return timezone.now() + timedelta(days=15)


class DiscountCart(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    text = models.CharField(max_length=255,unique=True)
    percentage = models.PositiveIntegerField(default=0)
    max_discount = models.DecimalField(max_digits=10, decimal_places=2)
    max_use = models.PositiveIntegerField(default=10)
    first_time = models.BooleanField(default=True)
    expired_time = models.DateTimeField(default=default_expired_time)
    product=models.ForeignKey(Product,on_delete=models.CASCADE,null=True,blank=True)
    payment_without_discount = models.DecimalField(max_digits=10, decimal_places=2,default=0)
    class Meta:
        constraints = [
            models.CheckConstraint(
                check=models.Q(percentage__gte=0, percentage__lte=100),
                name="valid_discount_range_cart",
            )
        ]

    def __str__(self):
        return f"{self.text} - {self.percentage}% for {self.user.username}"


class DeliverySlots(models.Model):
    start_time = models.TimeField()
    end_time = models.TimeField()
    delivery_date = models.DateField()
    max_orders = models.IntegerField()
    current_fill = models.IntegerField()
    shipping_fee=models.DecimalField(max_digits=10,decimal_places=2,default=0)


class Order(models.Model):
    PAYMENT_STATUSES = [
        ("unpaid", "پرداخت نشده"),
        ("paid", "پرداخت شده"),
        ("pending", "در حال بررسی"),
        ("failed", "ناموفق"),
    ]
    pay_status = models.CharField(
        max_length=20, choices=PAYMENT_STATUSES, default="unpaid"
    )
    location = models.ForeignKey(
        Location, on_delete=models.SET_NULL, null=True, blank=True
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    delivery = models.ForeignKey(DeliverySlots,on_delete=models.PROTECT)
    created_at = models.DateTimeField(default=timezone.now)
    discription = models.TextField(blank=True)
    total_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    profit = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    status = models.SmallIntegerField(default=0, db_index=True)
    discount = models.ForeignKey(
        DiscountCart, on_delete=models.PROTECT, blank=True, null=True
    )
    delivered_at = models.DateTimeField(null=True, blank=True) 
    ref_id=models.IntegerField(null=True,blank=True)
    reciver = models.CharField(max_length=255, null=True, blank=True)
    reciver_phone = models.CharField(max_length=20, null=True, blank=True)

    def save(self, *args, **kwargs):
        if self.status == 4:
            if (
                not self.delivered_at or self.pk is None
            ):  
                self.delivered_at = timezone.now()
        else:
            self.delivered_at = None 
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Order #{self.id} by {self.user.phonenumber}"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    product_discount = models.PositiveIntegerField(default=0)
    def __str__(self):
        return f"{self.quantity} x {self.product.name} (Order #{self.order.id})"
