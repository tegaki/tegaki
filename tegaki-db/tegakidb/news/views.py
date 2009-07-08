from django.shortcuts import render_to_response, get_object_or_404

from tegakidb.news.models import NewsItem

from tegakidb.util import render_to

@render_to('news/index.html')
def index(request):
    latest_news = NewsItem.objects.all().order_by('-pub_date')[:5]
    return {'latest_news': latest_news}

@render_to('news/detail.html')
def detail(request, news_item_id):
    news_item = get_object_or_404(NewsItem, pk=news_item_id)
    return {'news_item': news_item}

