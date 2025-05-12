from django.db import models
from django.utils import timezone
from django.contrib.auth import get_user_model
from product.models import *
from cart.models import *
import jdatetime
from django.utils import timezone
from datetime import timedelta
from users.models import Location
from order.models import DeliverySlots
User = get_user_model()

class BreadReservation(models.Model):
    PERIOD_CHOICES = [
        ("weekly", "Weekly"),
        ("monthly", "Monthly"),
    ]

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="bread_reservations"
    )
    period = models.CharField(max_length=10, choices=PERIOD_CHOICES)
    delivery=models.ForeignKey(DeliverySlots,on_delete=models.PROTECT, null=True, blank=True)
    active = models.BooleanField(default=True)
    auto_pay = models.BooleanField(default=False)
    location=models.ForeignKey(Location,on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"{self.user.phonenumber} reserved {self.quantity} x ({self.period})"

    @property
    def total_items(self):
        return self.box_type * self.quantity

    def next_delivery_date(self):
        if not self.delivery:
            return None
        base_date = self.delivery.delivery_date
        if self.period == "weekly":
            return base_date + timedelta(weeks=1)
        elif self.period == "monthly":
            return base_date + timedelta(days=30)
        return None


class ReserveItem(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    reserve = models.ForeignKey(BreadReservation,on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField(default=1)
