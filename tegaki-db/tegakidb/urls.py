from django.conf.urls.defaults import *
from django.contrib import admin
from django.conf import settings
admin.autodiscover()

urlpatterns = patterns('',
    (r'^tegaki/$', 'tegakidb.news.views.index'),        #this could be changed

    (r'^tegaki/news/', include('tegakidb.news.urls')),

    (r'^tegaki/users/', include('tegakidb.users.urls')),
    
    (r'^tegaki/hwdb/', include('tegakidb.hwdb.urls')),

    (r'^tegaki/admin/(.*)', admin.site.root),
    #(r'^admin/', include(admin.site.urls)), #this is Django 1.1 version 
)

# We serve static content through Django in DEBUG mode only.
# In production mode, the proper directory aliases (Alias directive in Apache)
# should be defined.
if settings.DEBUG:
    urlpatterns += patterns('',
    (r'^static/(?P<path>.*)$', 'django.views.static.serve',
            {'document_root': settings.MEDIA_ROOT, 'show_indexes': True}),
    (r'^dojo/(?P<path>.*)$', 'django.views.static.serve',
            {'document_root': settings.DOJO_ROOT, 'show_indexes': True}),
    (r'^webcanvas/(?P<path>.*)$', 'django.views.static.serve',
            {'document_root': settings.WEBCANVAS_ROOT, 'show_indexes': True}),
    )
