from django.db import models
from django.contrib import admin
from django.contrib.auth.models import User, UserManager


#this creates a custom User class that inherits all of the functionality of standard Django Users
#The only problem here is deleting a TegakiUser doesn't delete the Django user
class TegakiUser(User):
    n_handwriting_samples = models.IntegerField(blank=True)
    
    #this gives our User class all the standard User functionality (hashing passwds etc)
    objects = UserManager()

admin.site.register(TegakiUser)
