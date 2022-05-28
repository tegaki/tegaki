#from django import forms
from dojango import forms

from tegakidb.users.models import TegakiUser
from django.contrib.auth.models import User
from tegakidb.hwdb.models import *
from tegakidb.utils.models import *

FILTERS = (
    ("\u4e00-\u9fff", 'CJK'),
#    ('Chinese'),
#    ('Japanese'),
#    ('Korean'),
    )



#form for editing tegaki users
class CharacterSetForm(forms.ModelForm):
    """
    We use this form to create Character set objects, and update them.
    It creates the form from the CharacterSet model and adds the filter and range fields
    as a form of input.
    Filter takes in any input text and filters out (by default CJK) characters.
    Range takes in a range of the format
     e.g. "8,A..F,11"

    """
    filter_text = forms.CharField(required=False, widget=forms.widgets.Textarea(), label="Enter any text and the text will be filtered")
    filter = forms.ChoiceField(required=False, label="A regex for filtering submission text", choices=FILTERS)
    range = forms.CharField(required=False, widget=forms.widgets.Textarea(), label="Enter a range like: 8,10..15,17 is equivalent to 8,10,11,12,13,14,15,17")
    class Meta:
        model = CharacterSet
        exclude = ('id','user', 'characters')

    def __init__(self, *args, **kwargs):
        super(CharacterSetForm, self).__init__(*args, **kwargs)
        #self.fields['lang'].label = "Language"
        try:
            self.fields['lang'].label = "Language"
        except:
            pass

    def save(self, *args, **kwargs):
        m = super(CharacterSetForm, self).save(commit=False, *args, **kwargs)
        #print self.cleaned_data['range'], "___", self.cleaned_data['filter']
        if self.cleaned_data['range'] != "":
            m.set = CharacterSet.get_set_from_range_string(self.cleaned_data['range'])
            #print "in range:", m.set
            m.save_string()
        elif self.cleaned_data['filter_text'] != "":
            f = self.cleaned_data['filter']
            m.set = CharacterSet.get_set_with_filter(self.cleaned_data['filter_text'],f)
            #print "in filter:", m.set, f
            m.save_string()
        m.save()
        return m
