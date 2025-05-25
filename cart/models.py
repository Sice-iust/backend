from django.db import models
from django.contrib.auth import get_user_model
from product.models import *
from order.models import DeliverySlots
User = get_user_model()


class CartItem(models.Model):


    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="cart_items")
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1) 

    class Meta:
        unique_together = ("user", "product")

    @property
    def total_items(self):
        return self.product.box_type * self.quantity

    def __str__(self):
        return (
            f"{self.product.name} - {self.user.phonenumber} | "
            f"{self.quantity} x box of {self.product.box_type} = {self.total_items} items"
        )

class DeliveryCart(models.Model):
    user=models.ForeignKey(User,on_delete=models.CASCADE)
    delivery=models.ForeignKey(DeliverySlots,on_delete=models.PROTECT)
    