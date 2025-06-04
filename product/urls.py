from django.contrib import admin
from django.urls import path
from .views import *

urlpatterns = [
    path("nanzi/admin/product/create/", AdminProductView.as_view(),name='product-post'),
    path("product/<int:id>/", SingleProductView.as_view(),name='product-single'),
    path("product/comments/<int:id>/", SingleProductCommentsView.as_view()),
    path("nanzi/admin/product/delete/<int:id>", AdminSingleProductView.as_view(),name='admin-product-single'),
    path("user/rate/product/", RateView.as_view(),name='rate-view'),
    path("user/rate/product/<int:id>/", SingleRateView.as_view(),name='rate-add'),
    path("user/comment/product/<int:id>", ProductCommentView.as_view()),
    path("product/popular/", PopularProductView.as_view(),name='popular-products'),
    path("product/discount/", DiscountView.as_view(),name='discount-products'),
    path("product/all/", DiscountView.as_view(),name='all-products'),
    path("product/category/", CategoryView.as_view()),
    path("product/category/box/", CategoryBoxView.as_view(),name='category-box'),
    path("nanzi/admin/product/show/",AdminProductDisply.as_view()),
    path("nanzi/admin/product/filter/",AdminFilterProduct.as_view()),
    path("nanzi/admin/categories/name/",CategoryNameView.as_view()),
    path("nanzi/admin/category/create/",CategoryCreationView.as_view()),
    path("nanzi/admin/category/modify/<int:id>/",CategoryModifyView.as_view()),
]
