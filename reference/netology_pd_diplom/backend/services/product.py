class ProductOperation:

    @classmethod
    def convert_queryset_to_list(cls, queryset) -> list:
        products_data = []

        for product in queryset:
            product_info_data = []

            for product_info in product.product_infos.all():
                product_parameter_data = []

                for product_parameter in product_info.product_parameters.all():
                    product_parameter_data.append({
                        'parameter_name': product_parameter.parameter.name,
                        'value': product_parameter.value
                    })

                product_info_data.append({
                    'model': product_info.model,
                    'external_id': product_info.external_id,
                    'shop_name': product_info.shop.name,
                    'quantity': product_info.quantity,
                    'price': product_info.price,
                    'price_rrc': product_info.price_rrc,
                    'product_parameters': product_parameter_data
                })

            products_data.append({
                'name': product.name,
                'category': product.category.name,
                'product_infos': product_info_data
            })
        return products_data
