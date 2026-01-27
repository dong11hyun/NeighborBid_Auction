import os
from celery import Celery

# Django settings 모듈 설정
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

app = Celery('neighborbid')

# namespace='CELERY'는 setting.py에서 CELERY_ 로 시작하는 설정을 읽겠다는 뜻
app.config_from_object('django.conf:settings', namespace='CELERY')

# INSTALLED_APPS에서 tasks.py를 자동으로 찾음
app.autodiscover_tasks()

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
