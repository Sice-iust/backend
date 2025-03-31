from django.db import models
from django.contrib.auth import get_user_model
from product.models import *


User = get_user_model()


class CartItem(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="cart_items")
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    class Meta:
        unique_together = (
            "user",
            "product",
        )  
    def __str__(self):
        return f"{self.product.name} {self.user.phonenumber} "
