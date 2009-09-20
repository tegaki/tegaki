# coding: UTF-8
from django.shortcuts import render_to_response, get_object_or_404
from django.http import HttpResponse, HttpResponseRedirect
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse

from django.conf import settings

from tegakidb.users.models import TegakiUser

from django.utils import simplejson
from tegakidb.utils import render_to, datagrid_helper

from dojango.util import to_dojo_data
from dojango.decorators import json_response


from tegakidb.lianxi.models import *
from tegakidb.hwdb.forms import *

@login_required
@render_to('lianxi/index.html')
def index(request):
    """
    Home page of Lianxi
    """
#    return HttpResponse("hi")
    return {}

@login_required
@render_to('lianxi/assignments.html')
def assignments(request):
    """
    List all assignments
    """
    return {}


@login_required
@json_response
def assignments_datagrid(request):
    ### need to hand pick fields from Assignments, if some are None, need to pass back empty strings for dojo
    dojo_obs = []
    assignments, num = datagrid_helper(Assigment, request)
    for a in assignments:
        djob = {}
        #'id', 'user__username', 'country', 'lang', 'description', 'n_handwriting_samples'
        djob['id'] = a.id
        #djob['character__utf8'] = s.character.utf8()
        #djob['character__lang__description'] = s.character.lang.description
        #djob['date'] = s.date
        #djob['character_set__name'] = s.character_set.name
        #djob['user__username'] = s.user.username
        #if s.user.get_profile().show_handwriting_samples or request.user == s.user: 
            #only if they publicly display this charset
            #or it's their charset
        #    dojo_obs += [djob]
        #else:
        #    num = num -1
    return to_dojo_data(dojo_obs, identifier='id', num_rows=num)
