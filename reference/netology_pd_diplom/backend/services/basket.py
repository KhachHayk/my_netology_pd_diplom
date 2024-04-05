from backend.models import Order, User, OrderItem

from backend.serializers import OrderItemSerializer
from django.db.models import Q
from django.conf import settings

from backend.tasks import send_email


class BasketOperation:

    def __init__(self, user: User, items: list):
        self.user = user
        self.items = items

    def create(self):
        order, _ = Order.objects.get_or_create(user_id=self.user.id, state='basket')
        objects_created = 0

        for order_item in self.items:
            order_item.update({'order': order.pk})
            serializer = OrderItemSerializer(data=order_item)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            objects_created += 1
        order = Order.objects.get(id=order.pk)
        send_email.delay('Обновление статуса заказа', 'Заказ сформирован', [self.user.email])

        if not order.is_sent_notification:
            order.is_sent_notification = True
            order.save()

        return objects_created

    def update(self):
        basket, _ = Order.objects.get_or_create(user_id=self.user.id, state='basket')
        objects_updated = 0

        for order_item in self.items:
            objects_updated += OrderItem.objects.filter(
                order_id=basket.id, id=order_item['id']).update(quantity=order_item['quantity'])

        return objects_updated

    def delete(self):
        basket, _ = Order.objects.get_or_create(user_id=self.user.id, state='basket')
        query = Q()
        objects_deleted = False

        for order_item_id in self.items:
            query = query | Q(order_id=basket.id, id=order_item_id)
            objects_deleted = True

        if objects_deleted:
            deleted_count = OrderItem.objects.filter(query).delete()[0]

            return deleted_count
