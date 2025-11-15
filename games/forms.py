from django import forms
from .models import Game

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
