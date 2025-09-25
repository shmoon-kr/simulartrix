import os
import django
from celery import Celery

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'simul_site.settings')
django.setup()
app = Celery('simulartrix')
app.config_from_object("django.conf:settings",namespace="CELERY")

from django.conf import settings

from celery.schedules import crontab
# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.

app.conf.update(
    broker_url=f'redis://{settings.CACHE_SERVER}:6379/0',
    result_backend=f'redis://{settings.CACHE_SERVER}:6379/0',
    task_serializer='json',
    accept_content=['json'],  # Ignore other content
    worker_max_tasks_per_child=100,
    worker_max_memory_per_child=1024,
    result_serializer='json',
)

@app.on_after_configure.connect
def setup_periodic_tasks(sender: Celery, **kwargs):
    '''
    # Calls test('hello') every 10 seconds.
    sender.add_periodic_task(10.0, test.s('hello'), name='add every 10')

    # Calls test('hello') every 30 seconds.
    # It uses the same signature of previous task, an explicit name is
    # defined to avoid this task replacing the previous one defined.
    sender.add_periodic_task(30.0, test.s('hello'), name='add every 30')

    # Calls test('world') every 30 seconds
    sender.add_periodic_task(30.0, test.s('world'), expires=10)

    # Executes every Monday morning at 7:30 a.m.
    sender.add_periodic_task(
        crontab(hour=7, minute=30, day_of_week=1),
        test.s('Happy Mondays!'),
    )
    '''

    sender.add_periodic_task(
        # 10초당 한 틱
        10.0,
        test.s('Happy Mondays!'),
        name='test'
    )

# Load task modules from all registered Django apps.
app.autodiscover_tasks()

@app.task
def test(arg):
    print(arg)

@app.task(bind=True, ignore_result=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
