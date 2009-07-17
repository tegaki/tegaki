from django.conf.urls.defaults import *

urlpatterns = patterns('tegakidb.users.views',
    url(r'^$', 'user_list', name="users"),
    url(r'^list_datagrid/$', 'user_list_datagrid', name="user-list-datagrid"),
    url(r'^register/$', 'register', name="register"),
    url(r'^(?P<userid>\d+)/$', 'profile', name="user-profile"),
    url(r'^edit/(?P<userid>\d+)/$', 'edit_profile', name="user-edit-profile"),
)

