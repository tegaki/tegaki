from django.conf.urls.defaults import *

urlpatterns = patterns('tegakidb.news.views',
    (r'^$', 'index'),
    (r'^(?P<news_item_id>\d+)/$', 'detail'),
)

