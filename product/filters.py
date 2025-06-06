import django_filters
from .models import Product


class CharInFilter(django_filters.BaseInFilter, django_filters.CharFilter):
    pass


class ProductFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(lookup_expr="icontains")
    category = CharInFilter(field_name="category__category", lookup_expr="in", label="Filter by category names")
    box_type = django_filters.NumberFilter()
    discount = django_filters.NumberFilter(field_name="discount", lookup_expr="gt")

    class Meta:
        model = Product
        fields = ["category", "name", "box_type", "discount"]
