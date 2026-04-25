from django import forms
from .models import OwnerContract
from finance.models import MonthlySettlement

class OwnerContractForm(forms.ModelForm):
    class Meta:
        model = OwnerContract
        fields = ['owner', 'package_name', 'commission_rate', 'start_date', 'end_date', 'status', 'agreement_document']
        widgets = {
            'owner': forms.Select(attrs={'class': 'form-control select2'}),
            'package_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., Premium Management'}),
            'commission_rate': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'end_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'agreement_document': forms.FileInput(attrs={'class': 'form-control-file'}),
        }

class SettlementRemitForm(forms.ModelForm):
    class Meta:
        model = MonthlySettlement
        fields = ['remittance_proof']
        widgets = {
            'remittance_proof': forms.FileInput(attrs={'class': 'form-control-file'}),
        }
