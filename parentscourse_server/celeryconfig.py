from __future__ import absolute_import, unicode_literals

import os
from celery import Celery

# set the default Django settings module for the 'celery' program.
from parentscourse_server.config import version

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'parentscourse_server.settings')

app = Celery('parentscourse_server')
if version == "debug":
    app.conf.broker_url = 'redis://127.0.0.1:6379/2'
    app.conf.result_backend = 'redis://127.0.0.1:6379/3'
elif version == "test":
    app.conf.broker_url = 'redis://172.17.0.15:6379/2'
    app.conf.result_backend = 'redis://172.17.0.15:6379/3'
elif version == "ali_test":
    app.conf.broker_url = 'redis://:hbb123@39.97.229.202:6379/4'
    app.conf.result_backend = 'redis://:hbb123@39.97.229.202:6379/5'

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django app configs.
app.autodiscover_tasks()


@app.task(bind=True)
def debug_task(self):
    pass
    # print('Request: {0!r}'.format(self.request))
