from django_filters import rest_framework as filters
from backend.models import ProductInfo


class ProductFilter(filters.FilterSet):
    shop = filters.NumberFilter(field_name="shop")
    category = filters.NumberFilter(field_name="product__category")

    class Meta:
        model = ProductInfo
        fields = ["product__category", "shop"]
