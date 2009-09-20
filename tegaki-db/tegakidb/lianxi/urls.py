from django.conf.urls.defaults import *

urlpatterns = patterns('tegakidb.lianxi.views',
    url(r'^$', 'index', name="lianxi"),
    url(r'^assignments/$', 'assignments', name="lianxi-assignments"),
    url(r'^assignments_datagrid/$', 'assignments_datagrid', name="lianxi-assignments-datagrid"),
)


