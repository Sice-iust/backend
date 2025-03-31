from django.contrib import admin
from django.urls import path
from .views import *

urlpatterns = [
    path('mycart/',CartView.as_view()),
    path('change/<int:id>/',SingleCartView.as_view()),
]
