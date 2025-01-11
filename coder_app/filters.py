from django_filters import rest_framework as filters
from coder_app.models import Offer
from django.db.models import Q, Min


class OfferFilter(filters.FilterSet):
    creator_id = filters.NumberFilter(field_name="user_id")
    min_price = filters.NumberFilter(method="filter_min_price")
    max_price = filters.NumberFilter(method="filter_max_price")
    max_delivery_time = filters.NumberFilter(
        field_name="details__delivery_time_in_days", lookup_expr="lte"
    )
    search = filters.CharFilter(method="filter_search")

    class Meta:
        model = Offer
        fields = ["creator_id", "min_price", "max_price", "max_delivery_time"]

    def filter_min_price(self, queryset, name, value):
        """
        Filter offers by minimum price.
        """

        return queryset.annotate(min_price=Min("details__variant_price")).filter(
            min_price__gte=value
        )

    def filter_max_price(self, queryset, name, value):
        """
        Filter offers by maximum price.
        """

        return queryset.annotate(min_price=Min("details__variant_price")).filter(
            min_price__lte=value
        )

    def filter_search(self, queryset, name, value):
        """
        Filters offers by searching in the title and description fields.
        """

        return queryset.filter(
            Q(title__icontains=value) | Q(description__icontains=value)
        )
