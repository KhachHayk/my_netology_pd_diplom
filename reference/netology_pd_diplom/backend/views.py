import json

from distutils.util import strtobool
from drf_spectacular.utils import OpenApiParameter, extend_schema, inline_serializer
from rest_framework.request import Request
from rest_framework import serializers
from django.core.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from django.db.models import Sum, F
from django.http import JsonResponse
from rest_framework import generics
from rest_framework.viewsets import ModelViewSet
from rest_framework.authtoken.models import Token
from rest_framework.generics import ListAPIView, ListCreateAPIView
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import GenericViewSet

from backend.models import Shop, Category, Product, ProductInfo, Parameter, ProductParameter, Order, OrderItem, \
    Contact, ConfirmEmailToken
from backend.serializers import UserSerializer, CategorySerializer, ShopSerializer, ProductInfoSerializer, \
    OrderItemSerializer, OrderSerializer, ContactSerializer, UserRegisterSerializer, UserLoginSerializer, PartnerUpdateSerializer, OrderCreateSerializer, ContactCreateSerializer, ShopCreateSerializer, BasketCreateSerializer, ConfirmAccountSerializer, AccountDetailsCreateSerializer, BasketDeleteSerializer, BasketUpdateSerializer
from backend.filters import ProductFilter
from backend.services.basket import BasketOperation
from backend.services.contacts import ContactOperation
from backend.services.order import OrderOperation
from backend.permissions import ShopsOnly
from backend.tasks import do_import


class RegisterAccount(generics.CreateAPIView):
    """
    Для регистрации покупателей
    """
    serializer_class = UserRegisterSerializer


class ConfirmAccount(APIView):
    """
    Класс для подтверждения почтового адреса
    """

    # Регистрация методом POST
    def post(self, request, *args, **kwargs):
        """
        Подтверждает почтовый адрес пользователя.

        Args:
        - request (Request): The Django request object.

        Returns:
        - JsonResponse: The response indicating the status of the operation and any errors.
        """
        serializer = ConfirmAccountSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        token = ConfirmEmailToken.objects.filter(
            user__email=serializer.data['email'], key=serializer.data['token']).first()

        if not token:
            return JsonResponse({'Status': False, 'Errors': 'Неправильно указан токен или email'})

        token.user.is_active = True
        token.user.save()
        token.delete()

        return JsonResponse({'Status': True})


class AccountDetails(APIView):
    permission_classes = (IsAuthenticated,)
    """
    A class for managing user account details.

    Methods:
    - get: Retrieve the details of the authenticated user.
    - post: Update the account details of the authenticated user.

    Attributes:
    - None
    """

    # получить данные
    def get(self, request: Request, *args, **kwargs):
        """
        Retrieve the details of the authenticated user.

        Args:
        - request (Request): The Django request object.

        Returns:
        - Response: The response containing the details of the authenticated user.
        """
        serializer = UserSerializer(self.request.user)

        return Response(serializer.data)

    # Редактирование методом POST
    def post(self, request, *args, **kwargs):
        """
        Update the account details of the authenticated user.

        Args:
        - request (Request): The Django request object.

        Returns:
        - JsonResponse: The response indicating the status of the operation and any errors.
        """
        serializer = AccountDetailsCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        password = serializer.data.get("password")
        self.request.user.set_password(password)
        user_serializer = UserSerializer(request.user, data=request.data, partial=True)
        user_serializer.is_valid(raise_exception=True)
        user_serializer.save()

        return JsonResponse({'Status': True})


@extend_schema(
    request=inline_serializer(
        name="LoginSerializer",
        fields={
            "email": serializers.EmailField(),
            "password": serializers.CharField()
        }
    )
)
class LoginAccount(APIView):
    """
    Класс для авторизации пользователей
    """

    def post(self, request, *args, **kwargs):
        """
        Authenticate a user.

        Args:
            request (Request): The Django request object.

        Returns:
            JsonResponse: The response indicating the status of the operation and any errors.
        """
        serializer = UserLoginSerializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
            user = serializer.get_user(serializer.data)

            if user is not None and user.is_active:
                token, _ = Token.objects.get_or_create(user=user)

                return JsonResponse({'token': token.key})
            return JsonResponse({'Status': False, 'Errors': 'User not found or not active'})
        except ValidationError as e:

            return JsonResponse({'Status': False, 'Errors': e})


class CategoryView(ListAPIView):
    """
    Класс для просмотра категорий
    """
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = (IsAuthenticated,)


class ShopView(ListAPIView):
    """
    Класс для просмотра списка магазинов
    """
    queryset = Shop.objects.filter(state=True)
    serializer_class = ShopSerializer
    permission_classes = (IsAuthenticated,)


class ProductInfoView(GenericViewSet):
    permission_classes = (IsAuthenticated,)
    serializer_class = ProductInfoSerializer
    filterset_class = ProductFilter
    """
    A class for searching products.

    Methods:
    - get: Retrieve the product information based on the specified filters.

    Attributes:
    - None
    """

    def get_queryset(self):
        return (
            ProductInfo.objects
            .filter(shop__state=True)
            .select_related('shop', 'product__category')
            .prefetch_related('product_parameters__parameter').distinct()
        )

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="category", description="Category id", required=False
            ),
            OpenApiParameter(
                name="shop", description="shop_id", required=False
            ),
        ],
    )
    def list(self, request: Request, *args, **kwargs):
        """
        Retrieve the product information based on the specified filters.

        Args:
        - request (Request): The Django request object.

        Returns:
        - Response: The response containing the product information.
        """
        serializer = ProductInfoSerializer(
            self.filter_queryset(self.get_queryset()), many=True
        )

        return Response(serializer.data)


class BasketView(ModelViewSet):
    permission_classes = (IsAuthenticated,)

    """
    A class for managing the user's shopping basket.

    Methods:
    - get: Retrieve the items in the user's basket.
    - post: Add an item to the user's basket.
    - put: Update the quantity of an item in the user's basket.
    - delete: Remove an item from the user's basket.

    Attributes:
    - None
    """

    def get_queryset(self):
        return Order.objects.filter(
            user_id=self.request.user.id, state='basket').prefetch_related(
            'ordered_items__product_info__product__category',
            'ordered_items__product_info__product_parameters__parameter').annotate(
            total_sum=Sum(F('ordered_items__quantity') * F('ordered_items__product_info__price'))).distinct()

    def get_serializer_class(self):
        if self.request.method == "POST":
            return BasketCreateSerializer
        elif self.request.method == "DELETE":
            return BasketDeleteSerializer
        elif self.request.method == "PUT":
            return BasketUpdateSerializer
        return OrderSerializer

    def retrieve(self, request, *args, **kwargs):
        """
        Retrieve the items in the user's basket.

        Args:
        - request (Request): The Django request object.

        Returns:
        - Response: The response containing the items in the user's basket.
        """
        serializer = OrderSerializer(self.get_queryset(), many=True)

        return Response(serializer.data)

    def create(self, request, *args, **kwargs):
        serializer_class = self.get_serializer_class()
        serializer = serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        items = serializer.data.get("items")
        basket_operation = BasketOperation(self.request.user, items)
        objects_created = basket_operation.create()

        return JsonResponse({'Status': True, 'Создано объектов': objects_created})

    def destroy(self, request, *args, **kwargs):
        serializer_class = self.get_serializer_class()
        serializer = serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        items = serializer.data.get('items')
        basket_operation = BasketOperation(self.request.user, items)
        deleted_count = basket_operation.delete()

        return JsonResponse({'Status': True, 'Удалено объектов': deleted_count})

    def update(self, request, *args, **kwargs):
        """
        Update the items in the user's basket.

        Args:
        - request (Request): The Django request object.

        Returns:
        - JsonResponse: The response indicating the status of the operation and any errors.
        """
        serializer_class = self.get_serializer_class()
        serializer = serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        items = serializer.data.get('items')
        basket_operation = BasketOperation(self.request.user, items)
        updated_basket_items = basket_operation.update()

        return JsonResponse({'Status': True, 'Обновлено объектов': updated_basket_items})


class PartnerUpdate(generics.CreateAPIView):
    permission_classes = (IsAuthenticated, ShopsOnly)
    serializer_class = PartnerUpdateSerializer
    """
    A class for updating partner information.

    Methods:
    - post: Update the partner information.

    Attributes:
    - None
    """

    def post(self, request, *args, **kwargs):
        """
        Update the partner price list information.

        Args:
        - request (Request): The Django request object.

        Returns:
        - JsonResponse: The response indicating the status of the operation and any errors.
        """
        bytes_io_content = request.FILES.get("file").file.getvalue()
        serialized_content = bytes_io_content.decode('utf-8')
        json_data = json.dumps(serialized_content)
        do_import.delay(self.request.user.id, json_data)

        return JsonResponse({'Status': True})


class PartnerState(ListCreateAPIView):
    permission_classes = (IsAuthenticated, ShopsOnly)

    """
    A class for managing partner state.

    Methods:
    - get: Retrieve the state of the partner.

    Attributes:
    - None
    """

    def get_serializer_class(self):
        return ShopSerializer if self.request.method == "GET" else ShopCreateSerializer

    # получить текущий статус
    def list(self, request, *args, **kwargs):
        """
        Retrieve the state of the partner.

        Args:
        - request (Request): The Django request object.

        Returns:
        - Response: The response containing the state of the partner.
       """
        shop = request.user.shop
        serializer = ShopSerializer(shop)

        return Response(serializer.data)

    # изменить текущий статус
    def create(self, request, *args, **kwargs):
        """
        Update the state of a partner.

        Args:
        - request (Request): The Django request object.

        Returns:
        - JsonResponse: The response indicating the status of the operation and any errors.
        """
        serializer_class = self.get_serializer_class()
        serializer = serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        state = serializer.data.get('state')
        try:
            Shop.objects.filter(user_id=request.user.id).update(state=strtobool(state))
            return JsonResponse({'Status': True})
        except ValueError as error:
            return JsonResponse({'Status': False, 'Errors': str(error)})


class PartnerOrders(ListAPIView):
    permission_classes = (IsAuthenticated, ShopsOnly)
    serializer_class = OrderSerializer
    """
    Класс для получения заказов поставщиками
     Methods:
    - get: Retrieve the orders associated with the authenticated partner.

    Attributes:
    - None
    """

    def get_queryset(self):
        return Order.objects.filter(
            ordered_items__product_info__shop__user_id=self.request.user.id).exclude(state='basket').prefetch_related(
            'ordered_items__product_info__product__category',
            'ordered_items__product_info__product_parameters__parameter').select_related('contact').annotate(
            total_sum=Sum(F('ordered_items__quantity') * F('ordered_items__product_info__price'))).distinct()

    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)


class ContactView(ModelViewSet):
    permission_classes = (IsAuthenticated,)
    """
    A class for managing contact information.

    Methods:
    - get: Retrieve the contact information of the authenticated user.
    - post: Create a new contact for the authenticated user.
    - put: Update the contact information of the authenticated user.
    - delete: Delete the contact of the authenticated user.

    Attributes:
    - None
    """

    def get_queryset(self):
        return Contact.objects.filter(user_id=self.request.user.id)

    def get_serializer_class(self):
        if self.request.method == "GET":
            return ContactSerializer
        elif self.request.method == "POST":
            return ContactCreateSerializer

    # получить мои контакты
    def list(self, request, *args, **kwargs):
        """
        Retrieve the contact information of the authenticated user.

        Args:
        - request (Request): The Django request object.

        Returns:
        - Response: The response containing the contact information.
        """
        serializer_class = self.get_serializer_class()
        serializer = serializer_class(self.get_queryset(), many=True)

        return Response(serializer.data)

    # добавить новый контакт
    def create(self, request, *args, **kwargs):
        """
        Create a new contact for the authenticated user.

        Args:
        - request (Request): The Django request object.

        Returns:
        - JsonResponse: The response indicating the status of the operation and any errors.
        """

        serializer_class = self.get_serializer_class()
        serializer = serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        serializer_data = serializer.data
        contact_operation = ContactOperation(self.request.user)
        contact_operation.create(serializer_data)

        return JsonResponse({'Status': True})

    def update(self, request, *args, **kwargs):
        contact_id = self.request.parser_context.get("id")
        contact_operation = ContactOperation(self.request.user)
        contact_operation.update(contact_id, request.data)

        return JsonResponse({'Status': True})

    # удалить контакт
    def destroy(self, request, *args, **kwargs):
        """
        Delete the contact of the authenticated user.

        Args:
        - request (Request): The Django request object.

        Returns:
        - JsonResponse: The response indicating the status of the operation and any errors.
        """

        serializer_class = self.get_serializer_class()
        serializer = serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        items = request.data.get("items")
        contact_operation = ContactOperation(self.request.user)
        contact_operation.delete(items)


class OrderView(ModelViewSet):
    permission_classes = (IsAuthenticated,)
    """
    Класс для получения и размешения заказов пользователями
    Methods:
    - get: Retrieve the details of a specific order.
    - post: Create a new order.
    - put: Update the details of a specific order.
    - delete: Delete a specific order.

    Attributes:
    - None
    """

    def get_serializer_class(self):
        if self.request.method == "GET":
            return OrderSerializer
        else:
            return OrderCreateSerializer

    def get_queryset(self):
        return Order.objects.filter(
            user_id=self.request.user.id).exclude(state='basket').prefetch_related(
            'ordered_items__product_info__product__category',
            'ordered_items__product_info__product_parameters__parameter').select_related('contact').annotate(
            total_sum=Sum(F('ordered_items__quantity') * F('ordered_items__product_info__price'))).distinct()

    # получить мои заказы
    def list(self, request, *args, **kwargs):
        """
        Retrieve the details of user orders.

        Args:
        - request (Request): The Django request object.

        Returns:
        - Response: The response containing the details of the order.
        """
        serializer_class = self.get_serializer_class()
        serializer = serializer_class(self.get_queryset(), many=True)

        return Response(serializer.data)

    # разместить заказ из корзины
    def create(self, request, *args, **kwargs):
        """
        Put an order and send a notification.

        Args:
        - request (Request): The Django request object.

        Returns:
        - JsonResponse: The response indicating the status of the operation and any errors.
        """
        serializer_class = self.get_serializer_class()
        serializer = serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        order_operation = OrderOperation(self.request.user)
        order_json_response = order_operation.create(serializer.data)

        return order_json_response
