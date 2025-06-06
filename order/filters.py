import django_filters
from .models import Order


class OrderFilter(django_filters.FilterSet):
    delivery_date = django_filters.DateFilter(field_name="delivery__delivery_date")
    delivery_date__gte = django_filters.DateFilter(
        field_name="delivery__delivery_date", lookup_expr="gte"
    )
    delivery_date__lte = django_filters.DateFilter(
        field_name="delivery__delivery_date", lookup_expr="lte"
    )
    is_archive = django_filters.BooleanFilter(field_name="is_archive")
    is_admin_canceled = django_filters.BooleanFilter(field_name="is_admin_canceled")
    id = django_filters.NumberFilter(field_name="id")
    start_time__gte = django_filters.TimeFilter(
        field_name="delivery__start_time", lookup_expr="gte"
    )
    end_time__lte = django_filters.TimeFilter(
        field_name="delivery__end_time", lookup_expr="lte"
    )

    class Meta:
        model = Order
        fields = [
            "id",
            "delivery_date",
            "delivery_date__gte",
            "delivery_date__lte",
            "is_archive",
            "is_admin_canceled",
            "start_time__gte",
            "end_time__lte",
        ]
