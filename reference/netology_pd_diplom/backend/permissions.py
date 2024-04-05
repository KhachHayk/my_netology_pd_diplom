from rest_framework.permissions import BasePermission


class ShopsOnly(BasePermission):
    message = 'Только для магазинов!'

    def has_permission(self, request, view):
        return request.user.type == 'shop'
