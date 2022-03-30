from django import forms
from .models import Post



class PostForm(forms.ModelForm):
    class Meta:
            # На основе какой модели создаётся класс формы
            model = Post
            # Укажем, какие поля будут в форме
            fields = ('group', 'text') 