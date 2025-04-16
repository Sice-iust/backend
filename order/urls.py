from django.contrib import admin
from django.urls import path
from .views import *

urlpatterns = [
    path("user/discounts/", MyDiscountView.as_view()),
    path('admin/discount',AdminDiscountView.as_view()),
    path("admin/discount/<int:id>/", SingleDiscountCartView.as_view()),
    path("user/order/submit/", SubmitOrderView.as_view()),
    path("user/order/myorder/", OrderView.as_view()),
    path("admin/order/orders/", AllOrderView.as_view()),
]
