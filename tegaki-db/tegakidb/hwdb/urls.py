from django .conf.urls.defaults import *

urlpatterns = patterns('tegakidb.hwdb.views',
    url(r'^$', 'index', name="hwdb"),
    url(r'^input/$', 'input', name="hwdb-input"),
    url(r'^input_submit/$', 'input_submit', name="hwdb-input-submit"),
    url(r'^recognize/$', 'recognize', name="hwdb-recognize"),
    url(r'^recognize_submit/$', 'recognize_submit', name="hwdb-recognize-submit"),
    url(r'^samples/$', 'samples', name="hwdb-samples"),
    url(r'^view_sample/$', 'view_sample', name="hwdb-view-sample"),
    url(r'^samples_datagrid/$', 'samples_datagrid', name="hwdb-samples-datagrid"),
    url(r'^charsets/$', 'charsets', name="hwdb-charsets"),
    url(r'^charset_datagrid/$', 'charset_datagrid', name="hwdb-charset-datagrid"),
    url(r'^create_charset/$', 'create_charset', name="hwdb-create-charset"),
    url(r'^edit_charset/$', 'edit_charset', name="hwdb-edit-charset"),
    url(r'^select_charset/$', 'select_charset', name="hwdb-select-charset"),
    url(r'^view_charset/$', 'view_charset', name="hwdb-view-charset"),
    url(r'^random_char/$', 'random_char', name="hwdb-random-char"),
)
