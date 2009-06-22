# coding: UTF-8
from django.shortcuts import render_to_response, get_object_or_404
from django.http import HttpResponse, HttpResponseRedirect
from django.contrib.auth.decorators import login_required
from django.conf import settings

#from tegaki.character import Stroke, Point, Writing
from tegaki import character

from tegaki.recognizer import Recognizer

from tegakidb.hwdb.models import HandWritingSample, Character, CharacterSet
from tegakidb.users.models import TegakiUser

import simplejson


def index(request):
    return render_to_response('hwdb/index.html', {'utf8': ""})

@login_required #utilize django's built in login magic
def input(request):
    if settings.DEBUG:
        xml = request.REQUEST['xml']    #if testing we want to be able to pass stuff in with GET request
        utf8 = request.REQUEST['utf8']
    else:
        xml = request.POST['xml']
        utf8 = request.POST['utf8']

    user = request.user
    user = TegakiUser.objects.get(username=user.username)

    char = character.Character()
    char.set_utf8(utf8)
    char.read_string(xml)
    writing = char.get_writing()
    tdbChar = Character.objects.get(utf8=utf8)
    w = HandWritingSample(character=tdbChar, user=user, data=writing.to_xml())
    w.save() 
    return HttpResponse("%s" % w.id)

def sample(request):
    sample = "sample"
    return render_to_response('hwdb/sample.html', {'sample':sample})

def samples(request):
    hwrs = HandWritingSample.objects.all()
    s = ""
    for h in hwrs:
        s += "%s : %s" % (h.utf8, h.xml)
    return HttpResponse(s)

def recognize(request):
    if settings.DEBUG:
        xml = request.REQUEST['xml']    #if testing we want to be able to pass stuff in with GET request
    else:
        xml = request.POST['xml']
    char = character.Character()
    char.read_string(xml)
    klass = Recognizer.get_available_recognizers()['zinnia']
    rec = klass()
    rec.set_model('Simplified Chinese')
    writing = char.get_writing()
    #writing = writing.copy()
    results = rec.recognize(writing) 
    return HttpResponse(u"%s" % jsonify_results(results))

def jsonify_results(res):
    results = []
    for r in res:
        d = {"character":unicode(r[0], encoding='utf-8'), "score":r[1]}
        results += [d]
    s = simplejson.dumps(results, encoding='utf-8', ensure_ascii=False)
    return s



