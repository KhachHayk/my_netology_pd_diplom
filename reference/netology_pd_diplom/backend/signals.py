from typing import Type

from django.db.models.signals import post_save
from django.dispatch import receiver, Signal
from django_rest_passwordreset.signals import reset_password_token_created


from backend.models import ConfirmEmailToken, User, Order
from backend.tasks import send_email

new_user_registered = Signal()


@receiver(reset_password_token_created)
def password_reset_token_created(sender, instance, reset_password_token, **kwargs):
    """
    Отправляем письмо с токеном для сброса пароля
    When a token is created, an e-mail needs to be sent to the user
    :param sender: View Class that sent the signal
    :param instance: View Instance that sent the signal
    :param reset_password_token: Token Model Object
    :param kwargs:
    :return:
    """
    # send an e-mail to the user
    title = f"Password Reset Token for {instance.email}"
    send_email.delay(title, reset_password_token.key, instance.email)


@receiver(post_save, sender=User)
def new_user_registered_signal(sender: Type[User], instance: User, created: bool, **kwargs):
    """
    отправляем письмо с подтрердждением почты
    """
    if created and not instance.is_active:
        title = f"Password Reset Token for {instance.email}"
        # send an e-mail to the user
        token, _ = ConfirmEmailToken.objects.get_or_create(user_id=instance.pk)
        send_email.delay(title, token.key, instance.email)
