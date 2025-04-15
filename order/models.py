from django.db import models
from django.utils import timezone
from django.contrib.auth import get_user_model
from product.models import *
from cart.models import *
import jdatetime  
from django.utils import timezone
from datetime import timedelta

User = get_user_model()


def default_expired_time():
    return timezone.now() + timedelta(days=5)


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


class Order(models.Model):
    distination = models.CharField(max_length=200)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    delivery_time = models.DateTimeField()
    created_at = models.DateTimeField(default=timezone.now)
    discription = models.TextField(blank=True)
    total_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    status = models.SmallIntegerField(default=0, db_index=True)
    discount = models.ForeignKey(
        DiscountCart, on_delete=models.PROTECT, blank=True, null=True
    )
    shipping_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0) 
    def __str__(self):
        return f"Order #{self.id} by {self.user.phonenumber}"

    def get_jalali_delivery_day(self):
        jalali = jdatetime.datetime.fromgregorian(datetime=self.delivery_time)
        return jalali.strftime("%A %Y/%m/%d")

    def get_jalali_delivery_time(self):
        jalali = jdatetime.datetime.fromgregorian(datetime=self.delivery_time)
        return jalali.strftime("%H:%M")


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    product_discount = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"{self.quantity} x {self.product.name} (Order #{self.order.id})"
