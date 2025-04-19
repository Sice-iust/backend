from django.db import models
from django.contrib.auth import get_user_model
from product.models import *


User = get_user_model()


class CartItem(models.Model):
    BOX_CHOICES = [
        (1, "Box of 1"),
        (2, "Box of 2"),
        (4, "Box of 4"),
        (6, "Box of 6"),
        (8, "Box of 8"),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="cart_items")
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    box_type = models.PositiveIntegerField(choices=BOX_CHOICES)
    quantity = models.PositiveIntegerField(default=1) 

    class Meta:
        unique_together = ("user", "product", "box_type")

    @property
    def total_items(self):
        return self.box_type * self.quantity

    def __str__(self):
        return (
            f"{self.product.name} - {self.user.phonenumber} | "
            f"{self.quantity} x box of {self.box_type} = {self.total_items} items"
        )
