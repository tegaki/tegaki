from django.db import models
from django.contrib import admin
from django.contrib.auth.models import User, UserManager
from django.db.models.signals import post_save


#this creates a custom User class that inherits all of the functionality of standard Django Users
#The only problem here is deleting a TegakiUser doesn't delete the Django user
class TegakiUser(models.Model):
    user = models.ForeignKey(User, unique=True)
    #info    
    country = models.CharField(max_length=100, blank=True)
    lang = models.CharField(max_length=10, blank=True) #should be changed to lookup table
    description = models.TextField(blank=True)

    #preferences
    show_handwriting_samples = models.BooleanField(default=True) #should be default=False
    #stats
    n_handwriting_samples = models.IntegerField(blank=True, null=True)


#Creates the User profile automatically when a User is created
def create_profile(sender, **kw):
    user = kw["instance"]
    if kw["created"]:
        tu = TegakiUser(user=user)
        tu.save()
post_save.connect(create_profile, sender=User)

admin.site.register(TegakiUser)
