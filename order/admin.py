from django.contrib import admin
from .models import *

admin.site.register(DiscountCart)
admin.site.register(Order)
admin.site.register(OrderItem)
admin.site.register(DeliverySlots) 