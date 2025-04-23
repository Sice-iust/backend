from django.contrib import admin
from django.urls import path
from .views import *

urlpatterns = [
    path("sendotp/", SendOTPView.as_view()),
    path("login/", LoginVerifyOTPView.as_view()),
    path("profile/", ProfileView.as_view()),
    path("signup/", SignUpVerifyOTPView.as_view()),
    path("logout/", LogOutView.as_view()),
    path("profile/update/", UpdateProfileView.as_view()),
    path("locations/mylocation/", LocationView.as_view()),
    path("location/", NeshanLocationView.as_view()),
]
