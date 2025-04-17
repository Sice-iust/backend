from django.contrib import admin
from django.urls import path
from .views import *

urlpatterns = [
    path("user/cart/", CartView.as_view()),
    path("user/cart/modify/<int:id>/", SingleCartView.as_view()),
    path("header/", HeaderView.as_view()),
    path("user/discountcart/", DiscountedCartView.as_view()),
]
