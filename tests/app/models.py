"""
Models for tests
"""
from django.conf import settings
from django.db import models


class Entry(models.Model):
    title = models.CharField(max_length=255, default="Title")
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
