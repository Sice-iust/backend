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

class BreadReservation(models.Model):
    PERIOD_CHOICES = [
        ("weekly", "Weekly"),
        ("monthly", "Monthly"),
    ]

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="bread_reservations"
    )
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    period = models.CharField(max_length=10, choices=PERIOD_CHOICES)
    start_date = models.DateTimeField(default=timezone.now)
    active = models.BooleanField(default=True)
    auto_pay = models.BooleanField(default=False)
    location=models.ForeignKey(Location,on_delete=models.SET_NULL, null=True, blank=True)
    
    class Meta:
        unique_together = ("user", "product", "period")

    def __str__(self):
        return f"{self.user.phonenumber} reserved {self.quantity} x Box of {self.box_type} ({self.period})"

    @property
    def total_items(self):
        return self.box_type * self.quantity

    def next_delivery_date(self):
        if self.period == "weekly":
            return self.start_date + timezone.timedelta(weeks=1)
        elif self.period == "monthly":
            return self.start_date + timezone.timedelta(days=30)

