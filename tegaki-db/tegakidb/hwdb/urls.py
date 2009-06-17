from django .conf.urls.defaults import *

urlpatterns = patterns('tegakidb.hwdb.views',
    (r'^$', 'index'),
    (r'^input/$', 'input'),
    (r'^recognize/$', 'recognize'),
    (r'^samples/$', 'samples'),
)
