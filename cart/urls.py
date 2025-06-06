from django.contrib import admin
from django.urls import path
from .views import *

urlpatterns = [
    path("user/cart/", CartView.as_view(), name="cart"),
    path("user/cart/creat/<int:id>/", SingleCartView.as_view(), name='cart-single'),
    path("user/cart/modify/<int:id>/", SingleModifyCartView.as_view(),name='cart-single-modify'),
    path("header/", HeaderView.as_view(),name='header'),
    path("user/discountcart/", DiscountedCartView.as_view()),
    path("user/cart/quantity/", QuentityView.as_view(),name='quentity'),
    path("user/cart/delivery/", DeliveryView.as_view()),
    path("user/cart/delivery/create/<int:delivery_id>/", CartDeliveryView.as_view()),
]
