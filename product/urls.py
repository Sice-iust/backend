from django.contrib import admin
from django.urls import path
from .views import *

urlpatterns = [
    path("product/", ProductView.as_view()),
    path("product/<int:id>/", SingleProductView.as_view()),
    path("rate/", RateView.as_view()),
    path("rate/<int:id>/", SingleRateView.as_view()),
    path("product/popular/", PopularProductView.as_view()),
    path('product/discount/',DiscountView.as_view()),
]
