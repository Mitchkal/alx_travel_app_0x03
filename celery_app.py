#!/usr/bin/env python3
"""
celery configuration
"""

from __future__ import absolute_import, unicode_literals
import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'listings.settings')

app = Celery('listings')

app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()
