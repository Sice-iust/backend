from django.db import models
from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import (
    AbstractBaseUser,
    PermissionsMixin,
    Group,
    Permission,
)
from phonenumber_field.modelfields import PhoneNumberField
from datetime import timedelta,datetime
import random
from django.utils import timezone

class CustomUserManager(BaseUserManager):

    def create_user(self, username, email, phonenumber, password=None, **extra_fields):
        if not username or not email or not phonenumber:
            raise ValueError("Users must have a username, email, and phone number.")
        email = self.normalize_email(email)
        user = self.model(
            username=username, email=email, phonenumber=phonenumber,**extra_fields
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(
        self,
        username,
        email,
        phonenumber,
        password=None,
        city=None,
        **extra_fields,
    ):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        return self.create_user(username, email, phonenumber, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    username = models.CharField(max_length=100, unique=True, default="yourname")
    email = models.EmailField(max_length=100, unique=True, blank=True, null=True)
    firstname = models.CharField(max_length=50, blank=True, null=True)
    lastname = models.CharField(max_length=50, blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    phonenumber = PhoneNumberField(region="IR", unique=True)
    profile_photo = models.ImageField(
        upload_to="profiles",
        default="profiles/Default_pfp.jpg",
        null=False,
        blank=False,
    )

    password = models.CharField(max_length=100, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    date_joined = models.DateTimeField(auto_now_add=True)

    USERNAME_FIELD = "phonenumber"
    REQUIRED_FIELDS = ["username"]

    objects = CustomUserManager()

    groups = models.ManyToManyField(Group, related_name="custom_user_set", blank=True)
    user_permissions = models.ManyToManyField(
        Permission, related_name="custom_user_permissions_set", blank=True
    )

    def __str__(self):
        return str(self.phonenumber)


class Otp(models.Model):
    phonenumber = PhoneNumberField(region="IR")  
    otp = models.CharField(max_length=6, blank=True, null=True)
    otp_created_at = models.DateTimeField(
        default=timezone.now
    )  
    def generate_otp(self):
        self.otp = str(random.randint(1000, 9999))
        self.otp_created_at = timezone.now() 
        self.save()
        return self.otp

    def is_otp_valid(self):
        return self.otp_created_at and timezone.now() - self.otp_created_at < timedelta(
            minutes=2
        )

    def __str__(self):
        return f"{self.phonenumber} - {self.otp} ({self.otp_created_at})"
