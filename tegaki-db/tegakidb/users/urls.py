from django.conf.urls.defaults import *

urlpatterns = patterns('tegakidb.users.views',
    (r'^$', 'user_list'),
    (r'^register/$', 'register'),
    (r'^(?P<userid>\d+)/$', 'profile'),
)

