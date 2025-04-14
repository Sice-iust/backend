from django.contrib import admin
from django.urls import path
from .views import *

urlpatterns = [
    path('discount/',DiscountCartView.as_view()),
    path('discount/<int:id>/',SingleDiscountCartView.as_view()),
]
