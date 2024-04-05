from rest_framework import serializers

from backend.models import User, Category, Shop, ProductInfo, Product, ProductParameter, OrderItem, Order, Contact
from backend.validators import validate_password


class ContactSerializer(serializers.ModelSerializer):
    class Meta:
        model = Contact
        fields = ('id', 'city', 'street', 'house', 'structure', 'building', 'apartment', 'user', 'phone')
        read_only_fields = ('id',)
        extra_kwargs = {
            'user': {'write_only': True}
        }


class UserSerializer(serializers.ModelSerializer):
    contacts = ContactSerializer(read_only=True, many=True)

    class Meta:
        model = User
        fields = ('id', 'first_name', 'last_name', 'email', 'company', 'position', 'contacts')
        read_only_fields = ('id',)


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ('id', 'name',)
        read_only_fields = ('id',)


class ShopSerializer(serializers.ModelSerializer):
    class Meta:
        model = Shop
        fields = ('id', 'name', 'state',)
        read_only_fields = ('id',)


class ProductSerializer(serializers.ModelSerializer):
    category = serializers.StringRelatedField()

    class Meta:
        model = Product
        fields = ('name', 'category',)


class ProductParameterSerializer(serializers.ModelSerializer):
    parameter = serializers.StringRelatedField()

    class Meta:
        model = ProductParameter
        fields = ('parameter', 'value',)


class ProductInfoSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)
    product_parameters = ProductParameterSerializer(read_only=True, many=True)

    class Meta:
        model = ProductInfo
        fields = ('id', 'model', 'product', 'shop', 'quantity', 'price', 'price_rrc', 'product_parameters',)
        read_only_fields = ('id',)


class OrderItemSerializer(serializers.ModelSerializer):

    class Meta:
        model = OrderItem
        fields = ('id', 'product_info', 'quantity', 'order')
        read_only_fields = ('id',)
        extra_kwargs = {
            'order': {'write_only': True}
        }


class OrderItemCreateSerializer(OrderItemSerializer):
    product_info = ProductInfoSerializer(read_only=True)


class OrderSerializer(serializers.ModelSerializer):
    ordered_items = OrderItemCreateSerializer(read_only=True, many=True)

    total_sum = serializers.IntegerField()
    contact = ContactSerializer(read_only=True)

    class Meta:
        model = Order
        fields = ('id', 'ordered_items', 'state', 'dt', 'total_sum', 'contact',)
        read_only_fields = ('id',)


class OrderCreateSerializer(serializers.Serializer):
    id = serializers.IntegerField(required=True)
    contact = serializers.CharField(max_length=15, required=True)


class UserRegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, validators=[validate_password])

    def create(self, validated_data):
        user = User(
            username=validated_data['username'],
            email=validated_data['email'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
            company=validated_data['company'],
            position=validated_data['position'],
        )
        user.set_password(validated_data['password'])
        user.save()
        return user

    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email', 'password', 'company', 'position', 'username')
        extra_kwargs = {
            'first_name': {'required': True, 'allow_blank': False},
            'last_name': {'required': True, 'allow_blank': False},
            'email': {'required': True, 'allow_blank': False},
            'password': {'required': True, 'allow_blank': False},
            'company': {'required': True, 'allow_blank': False},
            'position': {'required': True, 'allow_blank': False},
            'user_name': {'required': True, 'allow_blank': False},
        }


class UserLoginSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    password = serializers.CharField(required=True)

    @staticmethod
    def get_user(data):
        email = data.get('email')
        password = data.get('password')

        if email and password:
            try:
                user = User.objects.get(email=email)
            except User.DoesNotExist:
                raise serializers.ValidationError("Пользователь с таким email не найден")

            if user.check_password(password):
                data['user'] = user
                return user
            else:
                raise serializers.ValidationError("Неверный пароль")

        return data


class PartnerUpdateSerializer(serializers.Serializer):
    file = serializers.FileField(required=True)


class ContactCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Contact
        fields = ("city", "street", "phone")


class ShopCreateSerializer(serializers.ModelSerializer):

    class Meta:
        model = Shop
        fields = ("state",)


class OrderItemsCreateSerializer(serializers.Serializer):
    product_info = serializers.PrimaryKeyRelatedField(queryset=ProductInfo.objects.all())
    quantity = serializers.IntegerField()
    order = serializers.IntegerField()


class OrderItemsUpdateSerializer(serializers.Serializer):
    product_info = serializers.PrimaryKeyRelatedField(queryset=ProductInfo.objects.all())
    quantity = serializers.IntegerField()
    order = serializers.PrimaryKeyRelatedField(queryset=Order.objects.all())
    id = serializers.PrimaryKeyRelatedField(queryset=OrderItem.objects.all())


class BasketCreateSerializer(serializers.Serializer):
    items = OrderItemsCreateSerializer(many=True)


class BasketUpdateSerializer(serializers.Serializer):
    items = OrderItemsUpdateSerializer(many=True)


class ConfirmAccountSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    token = serializers.CharField(required=True)


class AccountDetailsCreateSerializer(serializers.Serializer):
    password = serializers.CharField(required=True, validators=[validate_password])


class BasketDeleteSerializer(serializers.Serializer):
    items: int = serializers.ListField()
