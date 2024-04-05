from backend.models import Order, User

from django.db import IntegrityError
from django.http import JsonResponse
from backend.tasks import send_email


class OrderOperation:

    def __init__(self, user: User):
        self.user = user

    def create(self, data) -> JsonResponse:
        try:
            is_updated = Order.objects.filter(
                user_id=self.user.id, id=data['id']).update(
                contact_id=data['contact'],
                state='new')
        except IntegrityError as error:
            return JsonResponse({'Status': False, 'Errors': 'Неправильно указаны аргументы'})
        else:
            if is_updated:
                send_email.delay('Обновление статуса заказа', 'Заказ сформирован', [self.user.email])
                return JsonResponse({'Status': True})
            return JsonResponse({'Status': False})
