from __future__ import absolute_import, unicode_literals
import os
from celery import Celery

# Django'nun varsayılan ayar modülünü belirtiyoruz
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'companytracker.settings')

app = Celery('companytracker')

# Celery ayarlarını Django'nun ayarlarından alıyoruz
app.config_from_object('django.conf:settings', namespace='CELERY')

# Görevlerin otomatik olarak yüklenmesini sağlıyoruz
app.autodiscover_tasks()
