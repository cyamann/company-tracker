from __future__ import absolute_import, unicode_literals

# Celery uygulamasını içe aktarıyoruz
from .celery import app as celery_app

__all__ = ('celery_app',)
