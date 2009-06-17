# coding: UTF-8

from django.shortcuts import render_to_response, get_object_or_404
from django.http import HttpResponse, HttpResponseRedirect

from tegaki.character import Character, Stroke, Point, Writing
from tegaki.recognizer import Recognizer

from tegakidb.hwdb.models import HandWritingSample
try:
    import cPickle as pickle
except:
    import pickle



def index(request):
    return HttpResponse("index")

def input(request):
    return HttpResponse("input")

def sample(request):
    sample = "sample"
    return render_to_response('hwdb/sample.html', {'sample':sample})

def samples(request):
    hwrs = HandWritingSample.objects.all()
    s = ""
    for h in hwrs:
        s += "%s : %s" % (h.utf8, pickle.loads(h.pickled_char.decode('string_escape')).to_xml())
    return HttpResponse(s)

def recognize(request):
    #xml = cgi.escape(request.GET['xml'])
    utf8 = request.GET['utf8']
    xml = request.GET['xml']
    char = Character()
    char.set_utf8(utf8)
    #char.read('/vol/shufa/hwr/tegaki/tegaki/char2.xml')
    char.read_string(xml)
    klass = Recognizer.get_available_recognizers()['zinnia']
    rec = klass()
    rec.set_model('Simplified Chinese')
    writing = char.get_writing()
    w = HandWritingSample(utf8=char.get_utf8(), pickled_char=pickle.dumps(writing, pickle.HIGHEST_PROTOCOL).encode('string_escape'), xml=writing.to_xml())
    w.save() 
    #writing = writing.copy()
    results = rec.recognize(writing)   #this breaks! but should work 
    return HttpResponse("results: %s" % results)
#    return HttpResponse("rec: %s %s %s" % (rec._read_meta_file, rec._recognizer, rec._model))
  #  return HttpResponse("json: %s" % char.to_json())
