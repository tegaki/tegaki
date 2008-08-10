from django.conf.urls.defaults import *

urlpatterns = patterns('tegakidb.users.views',
    (r'^(?P<userid>\d+)/$', 'profile'),
)

