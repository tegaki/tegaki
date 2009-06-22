from django.shortcuts import render_to_response, get_object_or_404

#from django.contrib.auth.models import User
from tegakidb.users.models import TegakiUser

def profile(request, userid):
    user = get_object_or_404(TegakiUser, pk=userid)
    return render_to_response('users/profile.html', {'user': user})


