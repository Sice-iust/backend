from django.contrib import admin
from django.urls import path
from .views import *

urlpatterns = [
    path("mycart/", CartView.as_view()),
    path("change/<int:id>/", SingleCartView.as_view()),
    path("header/", HeaderView.as_view()),
    path("discount/", DiscountedCartView.as_view()),
]
