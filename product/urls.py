from django.contrib import admin
from django.urls import path
from .views import *

urlpatterns = [
    path("product/", ProductView.as_view()),
    path("nanzi/admin/product/create/", AdminProductView.as_view()),
    path("product/<int:id>/", SingleProductView.as_view()),
    path("product/comments/<int:id>/", SingleProductCommentsView.as_view()),
    path("nanzi/admin/product/delete/<int:id>", AdminSingleProductView.as_view()),
    path("user/rate/product/", RateView.as_view()),
    path("user/rate/product/<int:id>/", SingleRateView.as_view()),
    path("user/comment/product/<int:id>/", ProductCommentView.as_view()),
    path("product/popular/", PopularProductView.as_view()),
    path("product/discount/", DiscountView.as_view()),
    path("product/all/", DiscountView.as_view()),
    path("product/category/", CategoryView.as_view()),
]
