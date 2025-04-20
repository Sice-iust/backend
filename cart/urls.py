from django.contrib import admin
from django.urls import path
from .views import *

urlpatterns = [
    path("user/cart/", CartView.as_view()),
    path("user/cart/creat/<int:id>/", SingleCartView.as_view()),
    path("user/cart/modify/<int:id>/", SingleModifyCartView.as_view()),
    path("header/", HeaderView.as_view()),
    path("user/discountcart/", DiscountedCartView.as_view()),
    path("user/cart/quantity/<int:id>/", QuentityView.as_view()),
]
