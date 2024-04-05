import os
from celery import Celery
from django.core.wsgi import get_wsgi_application

a = os.environ['DJANGO_SETTINGS_MODULE'] = "netology_pd_diplom.settings"


app = Celery('netology_pd_diplom')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()
application = get_wsgi_application()
