from django.contrib import admin
from django.urls import path
from .views import *

urlpatterns = [
    path("user/discounts/", MyDiscountView.as_view()),
    path("nanzi/admin/discount/", AdminDiscountView.as_view()),
    path("nanzi/admin/discount/<int:id>/", SingleDiscountCartView.as_view()),
    path("user/order/submit/", SubmitOrderView.as_view()),
    path("api/payment/verify/", ZarinpalVerifyView.as_view(), name="zarinpal-verify"),
    path("user/order/myorder/", OrderView.as_view()),
    path("user/order/invoice/<int:id>", OrderInvoiceView.as_view()),
    path("nanzi/admin/order/orders/", AllOrderView.as_view()),
    path("user/delivery/", DeliverSlotView.as_view()),
    path("nanzi/admin/deliveryslot/", AdminDeliverySlot.as_view()),
    path("nanzi/admin/deliveryslot/<int:pk>/", SingleAdminDeliverySlot.as_view()),
    path("nanzi/admin/delivered/", AdminDeliveredOrder.as_view()),
    path("nanzi/admin/process/", AdminProcessing.as_view()),
    path("nanzi/admin/cancle/", AdminCancleView.as_view()),
    path("nanzi/status/change/<int:id>", ChangeStatusView.as_view()),
    path("nanzi/admin/order/id/", OrderIdView.as_view()),
]
