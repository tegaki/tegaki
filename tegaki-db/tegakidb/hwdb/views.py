from django.shortcuts import render_to_response, get_object_or_404
from django.http import HttpResponse, HttpResponseRedirect

from tegaki.character import Character, Stroke, Point, Writing
from tegaki.recognizer import Recognizer

def index(request):
    return HttpResponse("index")

def input(request):
    return HttpResponse("input")

def sample(request):
    sample = "sample"
    return render_to_response('hwdb/sample.html', {'sample':sample})

def recognize(request):
    #xml = cgi.escape(request.GET['xml'])
    xml = request.GET['xml']
    char = Character()
    #char.read('/vol/shufa/hwr/tegaki/tegaki/char2.xml')
    char.read_string(xml)
    klass = Recognizer.get_available_recognizers()['zinnia']
    rec = klass()
    rec.set_model('Simplified Chinese')
    writing = char.get_writing()
 
    #writing = writing.copy()
    results = rec.recognize(writing)   #this breaks! but should work 
    return HttpResponse("results: %s" % results)
#    return HttpResponse("rec: %s %s %s" % (rec._read_meta_file, rec._recognizer, rec._model))
  #  return HttpResponse("json: %s" % char.to_json())
