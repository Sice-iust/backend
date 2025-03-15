from django.contrib import admin
from django.urls import path
from .views import *

urlpatterns = [
    path("sendotp/", SendOTPView.as_view()),
    path('login/',VerifyOTPView.as_view()),
    path('profile/',ProfileView.as_view())
    ]

