#from django import forms
from dojango import forms

from tegakidb.users.models import TegakiUser
from django.contrib.auth.models import User
from tegakidb.hwdb.models import *

#form for editing tegaki users
class CharacterSetForm(forms.ModelForm):
    class Meta:
        model = CharacterSet
        exclude = ('id','user')

    def __init__(self, *args, **kwargs):
        super(CharacterSetForm, self).__init__(*args, **kwargs)
        self.fields['lang'].label = "Language"
        try:
            self.fields['lang'].label = "Language"
        except:
            pass


