from django.core.mail import EmailMultiAlternatives
from django.conf import settings
from backend.celery import app
from backend.services.loader import LoaderYaml


@app.task(bind=True, name="send_email")
def send_email(self, title: str, message: str,  to_email: list):
    msg = EmailMultiAlternatives(title, message, settings.EMAIL_HOST_USER, to_email)
    msg.send()


@app.task(bind=True, name="do_import")
def do_import(self, user_id: int, file_name: str) -> None:
    LoaderYaml(user_id).import_data(file_name)

