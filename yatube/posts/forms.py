from django import forms

from .models import Comment, Post


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ('text', 'group', 'image')

    def __init__(self, *args, **kwargs):
        super(PostForm, self).__init__(*args, **kwargs)
        self.fields['text'].widget.attrs['placeholder'] = (
            'Введите текст 🐱‍💻'
        )
        self.fields['group'].empty_label = (
            '(‾◡◝)'
        )

    def clean_text(self):
        data = self.cleaned_data['text']
        if 'блин' in data.lower():
            raise forms.ValidationError('Вы имели в виду "блинчик" 🥞?')
        return data


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ('text',)

    def __init__(self, *args, **kwargs):
        super(CommentForm, self).__init__(*args, **kwargs)
        self.fields['text'].widget.attrs['placeholder'] = (
            'Ваш комментарий может быть здесь ⊙.☉'
        )
