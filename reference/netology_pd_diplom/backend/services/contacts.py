from backend.models import User, Contact
from django.db.models import Q
from django.http import JsonResponse

from backend.serializers import ContactSerializer


class ContactOperation:

    def __init__(self, user: User):
        self.user = user

    def create(self, data) -> None:
        data._mutable = True
        data.update({'user': self.user.id})
        serializer = ContactSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

    def delete(self, items: str) -> JsonResponse:
        items_list = items.split(',')
        query = Q()
        objects_deleted = False
        for contact_id in items_list:
            if contact_id.isdigit():
                query = query | Q(user_id=self.user.id, id=contact_id)
                objects_deleted = True

        if objects_deleted:
            deleted_count = Contact.objects.filter(query).delete()[0]
            return JsonResponse({'Status': True, 'Удалено объектов': deleted_count})

    def update(self, contact_id: int, data):
        contact = Contact.objects.filter(id=contact_id, user_id=self.user.id).first()

        if not contact:
            return JsonResponse({'Status': False, "Error": 'Contact not found'})

        serializer = ContactSerializer(contact, data=data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
