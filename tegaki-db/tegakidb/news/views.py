from django.shortcuts import render_to_response, get_object_or_404

from tegakidb.news.models import NewsItem


def index(request):
    latest_news = NewsItem.objects.all().order_by('-pub_date')[:5]
    return render_to_response('news/index.html',
                              {'latest_news': latest_news})


def detail(request, news_item_id):
    news_item = get_object_or_404(NewsItem, pk=news_item_id)
    return render_to_response('news/detail.html', {'news_item': news_item})

