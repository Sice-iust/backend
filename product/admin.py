from django.contrib import admin
from .models import *

admin.site.register(Rate)
admin.site.register(Product)
admin.site.register(Subcategory)
admin.site.register(ProductComment)
admin.site.register(Category)
# admin.site.register(Discount)