from django.shortcuts import render_to_response, get_object_or_404
from django.http import HttpResponse, HttpResponseRedirect

#from django.contrib.auth.models import User
from tegakidb.users.models import TegakiUser
from tegakidb.users.forms import TegakiUserForm, RegisterForm

from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, authenticate

#@render_to: decorator for render_to_response, defined in tegakidb/__init__.py
#better place to put it?
from tegakidb.util import render_to

@render_to('users/register.html')
def register(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            new_user = form.save()
            user = authenticate(username=form.cleaned_data["username"], password=form.cleaned_data["password2"])
            login(request, user)
            return HttpResponseRedirect('/tegaki/news/') #TODO: add support for next redirection
    else:
        form = RegisterForm()
        #TODO: add support for next redirection
    
    return {'form':form}

@login_required
@render_to('users/profile.html')
def profile(request, userid):
    tu = get_object_or_404(TegakiUser, pk=userid)
    return {'tegaki_user': tu }

@login_required
@render_to('users/list.html')
def user_list(request):
    return {}
