from django.db import models
from django.contrib.auth import get_user_model
User = get_user_model()


class Product(models.Model):
    category = models.CharField(max_length=255)
    name = models.CharField(max_length=250, blank=False)
    price = models.DecimalField(
        max_digits=10, decimal_places=2
    )  
    description = models.TextField(blank=True)  
    photo = models.ImageField(upload_to="product") 
    average_rate = models.FloatField(default=0)
    discount = models.PositiveIntegerField(default=0)
    stock_1 = models.PositiveIntegerField(default=0)
    stock_2 = models.PositiveIntegerField(default=0)
    stock_4 = models.PositiveIntegerField(default=0)
    stock_6 = models.PositiveIntegerField(default=0)
    stock_8 = models.PositiveIntegerField(default=0)
    class Meta:
        constraints = [
            models.CheckConstraint(
                check=models.Q(discount__gte=0, discount__lte=100),
                name="valid_discount_range",
            )
        ]

    def __str__(self):
        return self.name

class Subcategory(models.Model):
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name="subcategories"
    )
    subcategory = models.CharField(max_length=100)

class Rate(models.Model):
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name="ratings"
    )
    rated_by = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="user_ratings"
    )
    rate = models.FloatField(default=1.0)

    class Meta:
        constraints = [
            models.CheckConstraint(
                check=models.Q(rate__gte=1, rate__lte=5), name="valid_rate_range"
            )
        ]

    def __str__(self):
        return f"{self.rated_by.username} rated {self.product.name} {self.rate}/5"

class ProductComment(models.Model):
    comment = models.TextField(max_length=None)
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name="comments" )
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="comments" )
    posted_at = models.DateTimeField(auto_now_add=True)
    suggested = models.BooleanField()
    class Meta:
        order_with_respect_to = ['product']
        ordering = ['-posted_at']
# class Discount(models.Model):
#     product = models.ForeignKey(
#         Product, on_delete=models.CASCADE, related_name="discounts"
#     )
#     percentage = models.PositiveIntegerField(default=0)

#     class Meta:
#         constraints = [
#             models.CheckConstraint(
#                 check=models.Q(percentage__gte=0, percentage__lte=100),
#                 name="valid_discount_range",
#             )
#         ]

#     def __str__(self):
#         return f"{self.percentage}% off on {self.product.name}"
