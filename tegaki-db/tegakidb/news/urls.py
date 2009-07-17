from django.conf.urls.defaults import *

urlpatterns = patterns('tegakidb.news.views',
    url(r'^$', 'index', name="news"),
    url(r'^(?P<news_item_id>\d+)/$', 'detail', name="detail"),
)

