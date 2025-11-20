from django import forms
from .models import Game, Comment


class GameForm(forms.ModelForm):
    class Meta:
        model = Game
        fields = ['title', 'release_year', 'genre', 'user_rating', 'cover']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'release_year': forms.NumberInput(attrs={'class': 'form-control'}),
            'genre': forms.TextInput(attrs={'class': 'form-control'}),
            'user_rating': forms.NumberInput(attrs={'class': 'form-control', 'min': 0, 'max': 10}),
            'cover': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }

    def clean_user_rating(self):
        rating = self.cleaned_data.get('user_rating')
        if rating is None:
            return 0
        if rating < 0 or rating > 10:
            raise forms.ValidationError("Rating musi być w zakresie 0–10.")
        return rating

class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['text']
        widgets = {
            'text': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Write a comment...'}),
        }
        labels = {
            'text': '',
        }

    def clean_text(self):
        text = self.cleaned_data.get('text', '').strip()
        if not text:
            raise forms.ValidationError("Comment cannot be empty.")
        if len(text) > 2000:
            raise forms.ValidationError("Comment is too long (max 2000 characters).")
        return text
