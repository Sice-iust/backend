from django.db import models
from django.contrib.auth import get_user_model
User = get_user_model()

class Category(models.Model):
    category = models.CharField(max_length=255, db_index=True)
    box_color = models.TextField(default="red")
    photo = models.ImageField(upload_to="category",null=True,blank=True)


class Product(models.Model):
    BOX_CHOICES = [
        (1, "Box of 1"),
        (2, "Box of 2"),
        (4, "Box of 4"),
        (6, "Box of 6"),
        (8, "Box of 8"),
    ]
    category = models.ForeignKey(
        Category, on_delete=models.CASCADE, related_name="product_category",null=True,blank=True
    )
    name = models.CharField(max_length=250, blank=False)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField(blank=True)
    photo = models.ImageField(upload_to="product")
    average_rate = models.FloatField(default=0, db_index=True)
    discount = models.PositiveIntegerField(default=0, db_index=True,null=True,blank=True)
    stock = models.PositiveIntegerField(default=0)
    box_type = models.PositiveIntegerField(choices=BOX_CHOICES, default=1)
    color = models.CharField(max_length=255, blank=True, null=True)

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
    SUGGESTED = 3
    NOT_SUGGESTED = 2
    NO_INFO = 1

    SUGGEST_STATUS = [
        (SUGGESTED, 'suggested'),
        (NOT_SUGGESTED, 'not suggested'),
        (NO_INFO, 'no information'),]
    
    comment = models.TextField(max_length=400)
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name="comments" )
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="comments" )
    posted_at = models.DateTimeField(auto_now_add=True)
    suggested = models.IntegerField(choices=SUGGEST_STATUS,default=NO_INFO)
    # class Meta:
    #     order_with_respect_to = 'product'
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
