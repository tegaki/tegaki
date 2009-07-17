from django .conf.urls.defaults import *

urlpatterns = patterns('tegakidb.hwdb.views',
    url(r'^$', 'index', name="hwdb"),
    url(r'^input/$', 'input', name="hwdb-input"),
    url(r'^recognize/$', 'recognize', name="hwdb-recognize"),
    url(r'^samples/$', 'samples', name="hwdb-samples"),
    url(r'^charset/$', 'select_charset', name="hwdb-charset"),
    url(r'^randomchar/$', 'random_char', name="hwdb-randomchar"),
)
