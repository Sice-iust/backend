from django.contrib import admin
from django.urls import path
from .views import *

urlpatterns = [
    path("user/wallet/", WalletView.as_view(), name="wallet"),
    path("user/wallet-verify/", WalletVerifyView.as_view(), name="wallet verify"),

]
