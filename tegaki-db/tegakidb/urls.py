from django.conf.urls.defaults import *
from django.contrib import admin

admin.autodiscover()

urlpatterns = patterns('',

    (r'^news/', include('tegakidb.news.urls')),

    (r'^users/', include('tegakidb.users.urls')),
    
    (r'^hwdb/', include('tegakidb.hwdb.urls')),

    (r'^admin/(.*)', admin.site.root),
    #(r'^admin/', include(admin.site.urls)), #this is Django 1.1 version 

)
