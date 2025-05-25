from django.contrib import admin
from django.urls import path
from .views import *
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

urlpatterns = [
    path("sendotp/", SendOTPView.as_view(), name="send-otp"),
    path("login/", LoginVerifyOTPView.as_view(), name="login"),
    path("profile/", ProfileView.as_view()),
    path("signup/", SignUpVerifyOTPView.as_view(), name="signup"),
    path("logout/", LogOutView.as_view(), name="logout"),
    path("profile/update/", UpdateProfileView.as_view(), name="update-profile"),
    path("locations/mylocation/", LocationView.as_view(), name="location"),
    path("location/", NeshanLocationView.as_view(),name="neshan-location"),
    path("locations/modify/<int:id>/", SingleLocationView.as_view(),name="location-detail"),
    path('locations/choose/location/<int:id>',ChooseLocationView.as_view(),name="choose-location"),
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

]
