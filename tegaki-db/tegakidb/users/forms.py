from django import forms

from tegakidb.users.models import TegakiUser
from django.contrib.auth.models import User

#form for editing tegaki users
class TegakiUserForm(forms.ModelForm):
    class Meta:
        model = TegakiUser
        exclude = ('user',)

    def __init__(self, *args, **kwargs):
        super(TegakiUserForm, self).__init__(*args, **kwargs)
        self.fields['lang'].label = "Language"
        try:
            self.fields['n_handwriting_samples'].label = "# of Handwriting Samples"
        except:
            pass 

#we don't want to let the user edit EVERYTHING about themselves
class SelfTUForm(TegakiUserForm):
    class Meta(TegakiUserForm.Meta):
        exclude = ('user', 'n_handwriting_samples')

class RegisterForm(SelfTUForm):
    username = forms.CharField(label="Username")
    password1 = forms.CharField(label="Password", widget=forms.PasswordInput)
    password2 = forms.CharField(label="Confirm Password", widget=forms.PasswordInput)

    def clean_username(self):
        username = self.cleaned_data["username"]
        try:
            User.objects.get(username=username)
        except User.DoesNotExist:
            return username
        raise forms.ValidationError("A user with that username already exists.")

    def clean_password2(self):
        password1 = self.cleaned_data.get("password1", "")
        password2 = self.cleaned_data["password2"]
        if password1 != password2:
            raise forms.ValidationError("The two password fields didn't match.")
        return password2

    #I hope I'm doing this right. It works but may not be the most elegant way.
    def save(self, commit=True):
        username = self.clean_username()
        password = self.clean_password2()
        new_user = User.objects.create(username=username)
        new_user.save()
        user = User.objects.get(username=username)
        user.set_password(password)
        user.save()
        self.instance.user_id = user.id
        forms.models.save_instance(self, user.get_profile(), commit=True)
        return user


