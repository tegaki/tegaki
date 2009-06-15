from django.conf.urls.defaults import *
from django.contrib import admin

admin.autodiscover()

urlpatterns = patterns('',

    (r'^admin/(.*)', admin.site.root),

    (r'^news/', include('tegakidb.news.urls')),

    (r'^users/', include('tegakidb.users.urls')),
    
    (r'^hwdb/', include('tegakidb.hwdb.urls')),
)
