from django.contrib import admin
from django.urls import path
from .views import *

urlpatterns = [
    path("user/discounts/", MyDiscountView.as_view()),
    path("nanzi/admin/discount/", AdminDiscountView.as_view()),
    path("nanzi/admin/discount/<int:id>/", SingleDiscountCartView.as_view()),
    path("user/order/submit/", SubmitOrderView.as_view()),
    path("user/order/myorder/", OrderView.as_view()),
    path("user/order/invoice/<int:id>", OrderInvoiceView.as_view()),
    path("nanzi/admin/order/orders/", AllOrderView.as_view()),
    path('user/delivery/',DeliverSlotView.as_view()),
    path("nanzi/admin/deliveryslot/", AdminDeliverySlot.as_view()),
    path("nanzi/admin/deliveryslot/<int:pk>/", SingleAdminDeliverySlot.as_view()),
]
