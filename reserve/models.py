# from django.db import models
# from django.utils import timezone
# from django.contrib.auth import get_user_model
# from product.models import *
# from cart.models import *
# import jdatetime
# from django.utils import timezone
# from datetime import timedelta
# from users.models import Location
# from order.models import DeliverySlots
# User = get_user_model()
# class ReserveDeliverySlots(models.Model):
#     start_time = models.TimeField()
#     end_time = models.TimeField()
#     delivery_date = models.DateField()
#     max_orders = models.IntegerField()
#     current_fill = models.IntegerField()
#     shipping_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)


# class Reservation(models.Model):
#     PERIOD_CHOICES = [
#         ("weekly", "Weekly"),
#         ("monthly", "Monthly"),
#     ]
#     PAYMENT_STATUSES = [
#         ("unpaid", "پرداخت نشده"),
#         ("paid", "پرداخت شده"),
#         ("pending", "در حال بررسی"),
#         ("failed", "ناموفق"),
#     ]
#     pay_status = models.CharField(
#         max_length=20, choices=PAYMENT_STATUSES, default="unpaid"
#     )
#     # user = models.ForeignKey(
#     #     User, on_delete=models.CASCADE, related_name="bread_reservations",db_index=True
#     # )
#     # product = models.ForeignKey(Product, on_delete=models.CASCADE)
#     quantity = models.PositiveIntegerField(default=1)
#     period = models.CharField(max_length=10, choices=PERIOD_CHOICES)
#     delivery = models.ForeignKey(
#         ReserveDeliverySlots, on_delete=models.PROTECT, null=True, blank=True
#     )
#     active = models.BooleanField(default=True)
#     # location=models.ForeignKey(Location,on_delete=models.SET_NULL, null=True, blank=True)
#     # date=models.DateTimeField(null=True,blank=True,auto_now=True)
#     class Meta:
#         unique_together = ("user", "period")

#     def __str__(self):
#         return f"{self.user.phonenumber} reserved {self.quantity} x ({self.period})"

#     @property
#     def total_items(self):
#         return self.box_type * self.quantity

#     def next_delivery_date(self):
#         if not self.delivery:
#             return None
#         base_date = self.delivery.delivery_date
#         if self.period == "weekly":
#             return base_date + timedelta(weeks=1)
#         elif self.period == "monthly":
#             return base_date + timedelta(days=30)
#         return None
