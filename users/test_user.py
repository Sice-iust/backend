import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()


from random import randint, choice
import random
import string
import json
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model
User = get_user_model()

def random_string(length=8):
    return ''.join(random.choices(string.ascii_letters, k=length))

def random_phonenumber():
    return f"+9811{random.randint(10000000, 99999999)}"

class UserTest():
    def setUp(self):
        self.username = random_string(10)
        self.phonenumber = random_phonenumber()
        self.email = f"{random_string(6)}@example.com"
        self.user = User.objects.create_user(
            username=self.username,
            password="commentpass",
            email=self.email,
            phonenumber=self.phonenumber)
        refresh = RefreshToken.for_user(self.user)
        self.access_token = str(refresh.access_token)

    def cleanUp(self):
        self.user.delete()