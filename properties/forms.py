"""
properties/forms.py
"""
from django import forms
from properties.models import Property, Unit, Location
from accounts.models import CustomUser


class PropertyForm(forms.ModelForm):
    class Meta:
        model = Property
        fields = ['name', 'address', 'location', 'owner']
        widgets = {
            'name':     forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Al-Noor Apartments'}),
            'address':  forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'location': forms.Select(attrs={'class': 'form-control'}),
            'owner':    forms.Select(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['owner'].queryset = CustomUser.objects.filter(role='OWNER', is_active=True)
        # If the user is a Manager (not Admin), lock owner to admins only
        if user and user.role == 'MANAGER':
            self.fields['owner'].queryset = CustomUser.objects.filter(role='OWNER', is_active=True)


class UnitForm(forms.ModelForm):
    class Meta:
        model = Unit
        fields = ['unit_number', 'unit_type', 'bedrooms', 'monthly_rent']
        widgets = {
            'unit_number':  forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. A1, Shop-2, 3rd Floor'}),
            'unit_type':    forms.Select(attrs={'class': 'form-control'}),
            'bedrooms':     forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'monthly_rent': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': 'PKR'}),
        }
