import os
from celery import Celery
from celery import shared_task  # Import shared_task

# Set the default Django settings module for Celery
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bus_booking.settings')

app = Celery('bus_booking')

# Load task modules from all registered Django apps.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Automatically discover tasks in installed apps
app.autodiscover_tasks()

app.conf.update(
    worker_pool='solo'  # This runs Celery workers without using multiple processes
)


@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
