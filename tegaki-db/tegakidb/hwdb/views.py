from django.shortcuts import render_to_response, get_object_or_404
from django.http import HttpResponse, HttpResponseRedirect

def index(request):
    return HttpResponse("index")

def input(request):
    return HttpResponse("input")

def sample(request):
    sample = "sample"
    return render_to_response('hwdb/sample.html', {'sample':sample})

def recognize(request):
    results = "blah"
    return HttpResponse("json: %s" % results)
