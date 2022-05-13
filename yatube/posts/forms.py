from django import forms

from django.utils.translation import gettext_lazy as _

from .models import Post


class PostForm(forms.ModelForm):
    class Meta:

        model = Post
        fields = ('group', 'text')

        labels = {
            'text': _('Текст нового поста'),
            'group': _('Группа'),
        }
        help_texts = {
            'text': _('Текст нового поста.'),
            'group': _('Группа, к которой будет относиться пост'),
        }
