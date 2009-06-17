from django.conf.urls.defaults import *
from django.contrib import admin

admin.autodiscover()

urlpatterns = patterns('',
    (r'^tegaki/$', 'tegakidb.news.views.index'),        #this could be changed

    (r'^tegaki/news/', include('tegakidb.news.urls')),

    (r'^tegaki/users/', include('tegakidb.users.urls')),
    
    (r'^tegaki/hwdb/', include('tegakidb.hwdb.urls')),

    (r'^tegaki/admin/(.*)', admin.site.root),
    #(r'^admin/', include(admin.site.urls)), #this is Django 1.1 version 

)
