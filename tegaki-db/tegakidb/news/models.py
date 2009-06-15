from django.db import models
from django.contrib.auth.models import User

class NewsItem(models.Model):

    class Admin:
        pass
 
    title = models.CharField(max_length=50)
    description = models.CharField(max_length=250)
    body = models.TextField()
    pub_date = models.DateTimeField('date published')
    user = models.ForeignKey(User)

    def __str__(self):
        return "%d - %s " % (self.id, self.title)
