from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class ZarinpalTransaction(models.Model):
    user = models.ForeignKey(User, on_delete=models.PROTECT)
    authority = models.CharField(max_length=64, unique=True, db_index=True)
    amount = models.PositiveIntegerField()
    status = models.CharField(max_length=20, default="pending")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["authority"]),
        ]
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user} | {self.amount} | {self.status}"
