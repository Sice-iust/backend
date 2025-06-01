from django.db import models
from django.contrib.auth import get_user_model
from order.models import Order

User = get_user_model()


class Ticket(models.Model):
    PRIORITY_CHOICES = [
        ("normal", "معمولی"),
        ("urgent", "فوری"),
        ("important", "مهم"),
    ]

    CATEGORY_CHOICES = [
        ("technical", "فنی"),
        ("other", "غیره"),
    ]

    user = models.ForeignKey(
        User, on_delete=models.PROTECT, db_index=True, related_name="user_tickets"
    )
    order = models.ForeignKey(Order, on_delete=models.PROTECT, null=True, blank=True)
    title = models.CharField(max_length=200)
    description = models.TextField()
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, db_index=True)
    category = models.CharField(max_length=10, choices=CATEGORY_CHOICES, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    admin_check = models.BooleanField(default=False)
    is_close = models.BooleanField(default=False)
    admin_answer = models.TextField(null=True, blank=True)

    admin_user = models.ForeignKey(
        User, on_delete=models.PROTECT, related_name="admin_tickets",null=True,blank=True
    )

    def __str__(self):
        return f"{self.title} - {self.get_priority_display()}"
