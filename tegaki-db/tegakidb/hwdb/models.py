from django.db import models
from django.contrib import admin

class HandWritingSample(models.Model):
    utf8 = models.CharField(max_length=2)
    pickled_char = models.TextField()
    xml = models.TextField()

admin.site.register(HandWritingSample)
