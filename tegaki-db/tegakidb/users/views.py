from django.shortcuts import render_to_response, get_object_or_404
from django.http import HttpResponse, HttpResponseRedirect

#from django.contrib.auth.models import User
from tegakidb.users.models import TegakiUser

"""
def login(request):
    username = request.POST['username']
    password = request.POST['password']
    user = authenticate(username=username, password=password)
    if user is not None:
        if user.is_active:
            tuser = TegakiUser.objects.get(username=user.username)
            login(request, tuser)
            # Redirect to a success page.
            if request.GET['next']:
                return HttpResponseRedirect( request.GET['next'] )
            else:
                return HttpResponseRedirect('/tegaki/')
        else:
            # Return a 'disabled account' error message
            return render_to_response('users/login.html', {})
    else:
        # Return an 'invalid login' error message. 
        render_to_response('users/login.html', {})

def logout(request):
"""    


def profile(request, userid):
    user = get_object_or_404(TegakiUser, pk=userid)
    return render_to_response('users/profile.html', {'user': user})


