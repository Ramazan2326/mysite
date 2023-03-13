from django.contrib.auth.forms import UserCreationForm
from django import forms
from .models import Contact
from django.contrib.auth import get_user_model
User = get_user_model()


class CreationForm(UserCreationForm):
    """ Creation form. """
    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('first_name', 'last_name', 'username', 'email')


class ContactForm(forms.ModelForm):
    """ Contact form. """
    class Meta:
        model = Contact
        fields = ('name', 'email', 'subject', 'body')
