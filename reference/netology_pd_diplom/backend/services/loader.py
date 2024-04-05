import abc

from yaml import safe_load
from backend.models import Shop, Category, Product, ProductInfo, ProductParameter, Parameter
import ruamel.yaml


class BaseLoader(abc.ABC):

    def __init__(self, user_id: int):
        self.user_id = user_id

    def import_data(self, url):
        ...


class LoaderYaml(BaseLoader):

    def import_data(self, data: str) -> None:
        yaml_str = safe_load(data)
        yaml = ruamel.yaml.YAML()
        data = yaml.load(yaml_str)

        shop, _ = Shop.objects.get_or_create(name=data['shop'], user_id=self.user_id)

        for category in data['categories']:
            category_object, _ = Category.objects.get_or_create(id=category['id'], name=category['name'])
            category_object.shops.add(shop.id)
            category_object.save()
        ProductInfo.objects.filter(shop_id=shop.id).delete()

        for item in data['goods']:
            product, _ = Product.objects.get_or_create(name=item['name'], category_id=item['category'])
            product_info = ProductInfo.objects.create(
                product_id=product.id,
                external_id=item['id'],
                model=item['model'],
                price=item['price'],
                price_rrc=item['price_rrc'],
                quantity=item['quantity'],
                shop_id=shop.id
            )

            for name, value in item['parameters'].items():
                parameter_object, _ = Parameter.objects.get_or_create(name=name)
                ProductParameter.objects.create(
                    product_info_id=product_info.id,
                    parameter_id=parameter_object.id,
                    value=value
                )


class LoaderJson(BaseLoader):
    ...
