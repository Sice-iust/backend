import django_filters
from .models import Product


class ProductFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(lookup_expr="icontains")
    category = django_filters.CharFilter(field_name="category__category", lookup_expr="iexact", label="Filter by category name")
    box_type = django_filters.NumberFilter()
    discount = django_filters.NumberFilter(field_name="discount", lookup_expr="gt")

    class Meta:
        model = Product
        fields = ["category", "name", "box_type", "discount"]
