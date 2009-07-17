from django.conf.urls.defaults import *
from django.contrib import admin
from django.conf import settings
admin.autodiscover()

urlpatterns = patterns('',
    url(r'^$', 'tegakidb.news.views.index', name="index"),        #this view could be changed
    url(r'^login/$', 'django.contrib.auth.views.login', {'template_name': 'users/login.html'}, name="login"),
    url(r'^logout/$', 'django.contrib.auth.views.logout', {'template_name': 'users/logout.html', 'next_page':'/%s' % settings.BASE_URL}, name="logout"),


    (r'^news/', include('tegakidb.news.urls')),

    (r'^users/', include('tegakidb.users.urls')),
    
    (r'^hwdb/', include('tegakidb.hwdb.urls')),




    (r'^dojango/', include('tegakidb.dojango.urls')),

    (r'^admin/(.*)', admin.site.root),
    #(r'^admin/', include(admin.site.urls)), #this is Django 1.1 version 
)

# We serve static content through Django in DEBUG mode only.
# In production mode, the proper directory aliases (Alias directive in Apache)
# should be defined.
if settings.DEBUG:
    urlpatterns += patterns('',
    (r'^static/webcanvas/(?P<path>.*)$', 'django.views.static.serve',
            {'document_root': settings.WEBCANVAS_ROOT, 'show_indexes': True}),

    (r'^static/(?P<path>.*)$', 'django.views.static.serve',
            {'document_root': settings.MEDIA_ROOT, 'show_indexes': True}),
    #(r'^dojo/(?P<path>.*)$', 'django.views.static.serve',
    #        {'document_root': settings.DOJO_ROOT, 'show_indexes': True}),
        )
