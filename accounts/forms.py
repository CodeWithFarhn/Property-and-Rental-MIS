"""
accounts/forms.py
Login form — styled for AdminLTE/Bootstrap 4.
"""
from django import forms


class LoginForm(forms.Form):
    username = forms.CharField(
        label='Email or Username',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Email or username',
            'autofocus': True,
            'id': 'id_username',
        })
    )
    password = forms.CharField(
        label='Password',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Password',
            'id': 'id_password',
        })
    )
