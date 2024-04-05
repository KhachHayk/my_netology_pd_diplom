from django.urls import path
from django_rest_passwordreset.views import reset_password_request_token, reset_password_confirm


from backend.views import PartnerUpdate, RegisterAccount, LoginAccount, CategoryView, ShopView, ProductInfoView, \
    BasketView, \
    AccountDetails, ContactView, OrderView, PartnerState, PartnerOrders, ConfirmAccount

details_methods = {"get": "retrieve", "put": "update", "delete": "destroy"}
list_create_methods = {"get": "list", "post": "create"}
full_methods = {"get": "list", "post": "create", "put": "update", "delete": "destroy"}

app_name = 'backend'


urlpatterns = [
    path('user/register', RegisterAccount.as_view(), name='user-register'),
    path('user/register/confirm', ConfirmAccount.as_view(), name='user-register-confirm'),
    path('user/login', LoginAccount.as_view(), name='user-login'),
    path('user/password_reset', reset_password_request_token, name='password-reset'),
    path('user/password_reset/confirm', reset_password_confirm, name='password-reset-confirm'),

    path('user/details', AccountDetails.as_view(), name='user-details'),
    path('user/contact', ContactView.as_view(list_create_methods), name='user-contact'),

    path('partner/update', PartnerUpdate.as_view(), name='partner-update'),
    path('partner/state', PartnerState.as_view(), name='partner-state'),
    path('partner/orders', PartnerOrders.as_view(), name='partner-orders'),

    path('basket', BasketView.as_view({"post": "create"}), name='basket'),
    path('basket/<int:pk>', BasketView.as_view(details_methods)),

    path('categories', CategoryView.as_view(), name='categories'),
    path('shops', ShopView.as_view(), name='shops'),
    path('products', ProductInfoView.as_view({"get": "list"}), name='products'),
    path('order', OrderView.as_view(list_create_methods), name='order'),
]
