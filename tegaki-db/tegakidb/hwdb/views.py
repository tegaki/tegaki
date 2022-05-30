# coding: UTF-8
from django.shortcuts import render_to_response, get_object_or_404
from django.http import HttpResponse, HttpResponseRedirect
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse

from django.conf import settings

#from tegaki.character import Stroke, Point, Writing
from tegaki import character

from tegaki.recognizer import Recognizer

from tegakidb.hwdb.models import *
from tegakidb.hwdb.forms import *
from tegakidb.users.models import TegakiUser

from django.utils import simplejson
from tegakidb.utils import render_to, datagrid_helper

from dojango.util import to_dojo_data
from dojango.decorators import json_response


@render_to('hwdb/index.html')
def index(request):
    return {'utf8': ""}


@login_required
@render_to('hwdb/input.html')
def input(request):
    charset = request.session.get('current_charset', None)
    if charset is None: #if they haven't selected a charset send them to the list
        return HttpResponseRedirect(reverse("hwdb-charsets"))

    #charlist = charset.get_list()
    char = request.GET.get('char', None)
    if char is not None:
        pass
    else:
        char = chr(charset.get_random())

    return {'char':char}


@login_required         #utilize django's built in login magic
def input_submit(request):
    if settings.DEBUG:
        xml = request.REQUEST['xml']    #if testing we want to be able to pass stuff in with GET request
        utf8 = request.REQUEST['utf8']
    else:
        xml = request.POST['xml']
        utf8 = request.POST['utf8']

    #if request.session.get('tegakiuser', None):
    user = request.user

    char = character.Character()
    char.set_utf8(utf8)
    char.read_string(xml)
    writing = char.get_writing()
    uni = ord(str(utf8))

    cs = request.session['current_charset']
    lang = cs.lang

    try:
        tdbChar = Character.objects.get(str=uni)  #this is the Character from the database
    except:
        tdbChar = Character(lang=lang, str=uni, n_handwriting_samples=1)
        tdbChar.save()
    w = HandWritingSample(character=tdbChar, user=user, data=writing.to_xml(), character_set=cs)  #minimum fields needed to store
    w.save()
    tdbChar.n_handwriting_samples += 1
    tdbChar.save()
    tu = user.get_profile()
    if tu.n_handwriting_samples:
        tu.n_handwriting_samples += 1
    else:
        tu.n_handwriting_samples = 1
    tu.save()
    return HttpResponse("%s" % w.id)

@render_to('hwdb/samples.html')
def samples(request):
    return {}

@login_required
@json_response
def samples_datagrid(request):
    ### need to hand pick fields from TegakiUser, if some are None, need to pass back empty strings for dojo
    dojo_obs = []
    samples, num = datagrid_helper(HandWritingSample, request)
    for s in samples:
        djob = {}
        #'id', 'user__username', 'country', 'lang', 'description', 'n_handwriting_samples'
        djob['id'] = s.id
        djob['character__utf8'] = s.character.utf8()
        djob['character__lang__description'] = s.character.lang.description
        djob['date'] = s.date
        djob['character_set__name'] = s.character_set.name
        djob['user__username'] = s.user.username
        if s.user.get_profile().show_handwriting_samples or request.user == s.user: 
            #only if they publicly display this charset
            #or it's their charset
            dojo_obs += [djob]
        else:
            num = num -1
    return to_dojo_data(dojo_obs, identifier='id', num_rows=num)


@login_required
@render_to('hwdb/view_sample.html')
def view_sample(request):
    id = request.REQUEST.get('id')
    sample = get_object_or_404(HandWritingSample, id=id)
    if sample.user == request.user:
        pass    #no editing of samples for now
    elif not request.user.get_profile().show_handwriting_samples:  
        #check that people don't try to see private samples
        return HttpResponseRedirect(reverse("hwdb-samples"))

    char = character.Character()
    char.set_utf8(sample.character)
    #here we should actually check to see if sample.data is compressed first
    xml = "<?xml version=\"1.0\" encoding=\"UTF-8\"?><character>%s</character>" % sample.data
    char.read_string(xml) #later need to check for compression
    writing = char.get_writing()
    json = writing.to_json()
    print(json)

    return {'sample':sample, 'char':char.get_utf8(), 'json':json}




@login_required
@render_to('hwdb/create_charset.html')
def create_charset(request):
    if request.method == 'POST':
        form = CharacterSetForm(request.POST)
        if form.is_valid():
            charset = form.save()
            charset.user = request.user #to be changed later where admins can assign users
            charset.save()
            request.session['current_charset'] = charset
            return HttpResponseRedirect(reverse("hwdb-charsets")) #TODO: add support for next redirection
    else:
        form = CharacterSetForm()

    return {'form':form}

@login_required
@render_to('hwdb/create_charset.html')
def create_random_charset(request):
    return {}


@login_required
@render_to('hwdb/charsets.html')
def charsets(request):
    return {}

@login_required
@json_response
def charset_datagrid(request):
    ### need to hand pick fields from TegakiUser, if some are None, need to pass back empty strings for dojo
    dojo_obs = []
    charsets, num = datagrid_helper(CharacterSet, request)
    for c in charsets:
        print(c)
        djob = {}
        #'id', 'user__username', 'country', 'lang', 'description', 'n_handwriting_samples'
        djob['id'] = c.id
        djob['name'] = c.name
        djob['lang__description'] = c.lang.description
        djob['description'] = c.description
        #print c.get_random()
        djob['random_char'] = chr(c.get_random())
        #djob['characters'] = c.characters       #might want to do something else for display
        djob['number_of_characters'] = len(c)
        if c.user:
            djob['user__username'] = c.user.username
        if c.public or request.user == c.user:  #only if they publicly display this charset
                                                #or it's their charset
            dojo_obs += [djob]
        else:
            num = num -1
    return to_dojo_data(dojo_obs, identifier='id', num_rows=num)

@login_required
def select_charset(request):
    id = request.REQUEST.get('id')      #checks both POST and GET fields
    request.session['current_charset'] = get_object_or_404(CharacterSet, id=id)
    return HttpResponse(request.session['current_charset'].name)

@login_required
@render_to('hwdb/view_charset.html')
def view_charset(request):
    id = request.REQUEST.get('id')
    cs = get_object_or_404(CharacterSet, id=id)
    if cs.user == request.user:
        return HttpResponseRedirect("%s?id=%d" % (reverse("hwdb-edit-charset"), int(id)))
    elif not cs.public:  #check that people don't try to see private charsets
        return HttpResponseRedirect(reverse("hwdb-charsets"))
    return {'charset':cs}

@login_required
@render_to('hwdb/edit_charset.html')
def edit_charset(request):
    id = request.REQUEST.get('id')
    cs = get_object_or_404(CharacterSet, id=id)
    if request.method == 'POST':
        form = CharacterSetForm(request.POST, instance=cs)
        if form.is_valid():
            charset = form.save()
            request.session['current_charset'] = charset
            #return HttpResponseRedirect(reverse("hwdb-charset"))
    else:
        form = CharacterSetForm(instance=cs)

    return {'form':form, 'charset':cs }




@login_required
def random_char(request):
    charset = request.session.get('current_charset', None)
    if charset is not None:
        return HttpResponse(chr(charset.get_random()))
    else:
        return HttpResponse("no charset selected")

@login_required
def random_charset(request):
    request.session['current_charset'] = CharacterSet.objects.get(id=1) #should be random
    return HttpResponse(request.session['current_charset'].name)

@render_to('hwdb/recognize.html')
def recognize(request):
    return {}

def recognize_submit(request):
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
    return HttpResponse("%s" % jsonify_results(results))

def jsonify_results(res):
    results = []
    for r in res:
        d = {"character":str(r[0], encoding='utf-8'), "score":r[1]}
        results += [d]
    s = simplejson.dumps(results, encoding='utf-8', ensure_ascii=False)
    return s



