from django.conf.urls.defaults import *

urlpatterns = patterns('',

    (r'^admin/', include('django.contrib.admin.urls')),

    (r'^news/', include('tegakidb.news.urls')),
)
