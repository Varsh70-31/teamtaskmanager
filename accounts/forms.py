from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model

from .models import User


class SignupForm(UserCreationForm):
    role = forms.ChoiceField(
        choices=User.ROLE_CHOICES,
        widget=forms.RadioSelect,
        initial='tasker',
        label='Account type',
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Ensure placeholders are present even when initial data is provided
        self.fields['username'].widget.attrs.setdefault('placeholder', 'your username')
        self.fields['email'].widget.attrs.setdefault('placeholder', 'you@example.com')
        self.fields['password1'].widget.attrs.setdefault('placeholder', '*******')
        self.fields['password2'].widget.attrs.setdefault('placeholder', '*******')

    class Meta:
        model = User
        fields = ['username', 'email', 'role', 'password1', 'password2']
        widgets = {
            'username': forms.TextInput(attrs={'placeholder': 'your username'}),
            'email': forms.EmailInput(attrs={'placeholder': 'you@example.com'}),
            'password1': forms.PasswordInput(attrs={'placeholder': '*******'}),
            'password2': forms.PasswordInput(attrs={'placeholder': '*******'}),
        }


class LoginForm(forms.Form):
    username = forms.CharField(max_length=150, widget=forms.TextInput(attrs={'placeholder': 'your username or email'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'placeholder': '*******'}))
    role = forms.ChoiceField(
        choices=User.ROLE_CHOICES,
        widget=forms.RadioSelect,
        initial='tasker',
        label='Login as',
    )
