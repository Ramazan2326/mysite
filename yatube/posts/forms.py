from .models import Post, Comment
from django import forms


class PostForm(forms.ModelForm):
    class Meta:
        """ Post form for creating a form for working with the User model. """
        model = Post
        fields = ('text', 'group', 'image')


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ('text',)
        labels = {
            'text': 'Текст',
        }
        help_texts = {
            'text': 'Текст нового комментария',
        }
