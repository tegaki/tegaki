from django.shortcuts import render_to_response, get_object_or_404
from django.http import HttpResponse, HttpResponseRedirect
from django.core.urlresolvers import reverse

#from django.contrib.auth.models import User
from tegakidb.users.models import *
from tegakidb.users.forms import *

from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, authenticate

#@render_to: decorator for render_to_response
from tegakidb.utils import render_to, datagrid_helper

from dojango.util import to_dojo_data
from dojango.decorators import json_response


@render_to('users/register.html')
def register(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            new_user = form.save()
            user = authenticate(username=form.cleaned_data["username"], password=form.cleaned_data["password2"])
            login(request, user)
            return HttpResponseRedirect(reverse("news")) #TODO: add support for next redirection
    else:
        form = RegisterForm()
        #TODO: add support for next redirection
    
    return {'form':form}

@login_required
@render_to('users/profile.html')
def profile(request, userid):
    tu = get_object_or_404(TegakiUser, pk=userid)
    if tu.user == request.user:
        return HttpResponseRedirect(reverse('user-edit-profile', args=[userid]))
    else:
        return {'tegaki_user':tu}

@login_required
#need a permission decorator here
@render_to('users/edit_profile.html')
def edit_profile(request, userid):
    tu = get_object_or_404(TegakiUser, pk=userid)
    if request.method == 'POST':
        data = request.POST
        if tu.user == request.user:
            form = SelfTUForm(data=data, instance=tu)
        else:
            form = TegakiUserForm(data=data, instance=tu)
        if form.is_valid():
            form.save()

    else:
        if tu.user == request.user:
            form = SelfTUForm(instance=tu)
        else:
            form = TegakiUserForm(instance=tu)

    return {'tegaki_user':tu, 'form':form }

@login_required
@render_to('users/list.html')
def user_list(request):
    return {}




@login_required
@json_response
def user_list_datagrid(request):
    ### need to hand pick fields from TegakiUser, if some are None, need to pass back empty strings for dojo
    dojo_obs = []
    users, num = datagrid_helper(TegakiUser, request)
    for u in users:
        djob = {}
        #'id', 'user__username', 'country', 'lang', 'description', 'n_handwriting_samples'
        djob['id'] = u.user.id
        djob['user__username'] = u.user.username
        if u.country:
            djob['country'] = u.country
        if u.lang:
            djob['lang__description'] = u.lang.description
        if u.description:
            djob['description'] = u.description
        if u.show_handwriting_samples:  #only if they publicly display their samples
            djob['n_handwriting_samples'] = u.n_handwriting_samples
        dojo_obs += [djob]
    return to_dojo_data(dojo_obs, identifier='user__username', num_rows=num)

    
