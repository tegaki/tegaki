# -*- coding: utf-8 -*-
from django.db import models
from django.contrib import admin

class Language(models.Model):
    """
    Store langauge codes (subtags) and their descriptions
    http://www.iana.org/assignments/language-subtag-registry
    """
    subtag = models.CharField(max_length=10)
    description = models.TextField()

    def __unicode__(self):
        return self.subtag
admin.site.register(Language)

"""
class Filter(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField()
    filter = models.CharField(max_length=255) #regex of which characters to filter

    def __unicode__(self):
            return self.name
admin.site.register(Filter)
"""
