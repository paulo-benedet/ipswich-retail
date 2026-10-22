from django import forms
from django.contrib.auth.forms import AuthenticationForm


class CustomerAuthenticationForm(AuthenticationForm):
    username = forms.EmailField(label="Email address", widget=forms.EmailInput(attrs={
        "autocomplete": "username", "placeholder": "you@example.com", "autofocus": True,
    }))
    password = forms.CharField(label="Password", strip=False, widget=forms.PasswordInput(attrs={
        "autocomplete": "current-password", "placeholder": "Enter your password",
    }))
    error_messages = {
        "invalid_login": "The email address or password is incorrect.",
        "inactive": "The email address or password is incorrect.",
    }
