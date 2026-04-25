"""
tenants/forms.py
"""
import re
from django import forms
from tenants.models import Tenant
from properties.models import Property, Unit
from tenants.services import clean_cnic, check_cnic_exists


FIELD_CLASSES = {'class': 'form-control'}


class TenantAdmissionForm(forms.Form):
    """
    Combined Tenant + Lease admission form.
    Both sections submit together as one atomic transaction.
    """
    # ── Section A: Tenant Details ──────────────────────────────────
    full_name         = forms.CharField(max_length=200, widget=forms.TextInput(attrs={**FIELD_CLASSES}))
    email             = forms.EmailField(widget=forms.EmailInput(attrs={**FIELD_CLASSES}))
    phone             = forms.CharField(max_length=20, widget=forms.TextInput(attrs={**FIELD_CLASSES, 'placeholder': '+92...'}))
    cnic              = forms.CharField(max_length=15, widget=forms.TextInput(attrs={
        **FIELD_CLASSES, 'placeholder': 'XXXXX-XXXXXXX-X or 13 digits',
        'hx-get': '/tenants/check-cnic/', 'hx-trigger': 'keyup changed delay:500ms, blur',
        'hx-target': '#cnic-feedback', 'hx-include': '[name=cnic]',
    }))
    profession        = forms.CharField(max_length=100, required=False, widget=forms.TextInput(attrs={**FIELD_CLASSES}))
    emergency_contact = forms.CharField(max_length=200, required=False, widget=forms.TextInput(attrs={**FIELD_CLASSES}))
    id_document       = forms.FileField(required=False, widget=forms.ClearableFileInput(attrs={'class': 'form-control-file'}))

    # ── Section B: Lease & Unit Assignment ────────────────────────
    property   = forms.ModelChoiceField(
        queryset=Property.objects.filter(status='ACTIVE'),
        empty_label='— Select Property —',
        widget=forms.Select(attrs={
            **FIELD_CLASSES,
            'hx-get': '/properties/units/vacant/', 'hx-target': '#id_unit',
            'hx-swap': 'innerHTML',
            'hx-trigger': 'change', 'hx-include': '[name=property]',
        })
    )
    unit = forms.ModelChoiceField(
        queryset=Unit.objects.none(),
        empty_label='— Select Unit —',
        widget=forms.Select(attrs={
            **FIELD_CLASSES,
            'hx-get': '/properties/units/info/', 'hx-target': '#unit-info-box',
            'hx-trigger': 'change', 'hx-include': '[name=unit]',
        })
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'property' in self.data:
            try:
                property_id = int(self.data.get('property'))
                self.fields['unit'].queryset = Unit.objects.filter(property_id=property_id, status='VACANT')
            except (ValueError, TypeError):
                pass
    start_date     = forms.DateField(widget=forms.DateInput(attrs={**FIELD_CLASSES, 'type': 'date'}))
    end_date       = forms.DateField(required=False, widget=forms.DateInput(attrs={**FIELD_CLASSES, 'type': 'date'}))
    month_to_month = forms.BooleanField(required=False, initial=False, widget=forms.CheckboxInput(attrs={'class': 'custom-control-input'}))
    monthly_rent   = forms.DecimalField(max_digits=12, decimal_places=2, widget=forms.NumberInput(attrs={**FIELD_CLASSES, 'step': '0.01'}))
    deposit_amount = forms.DecimalField(max_digits=12, decimal_places=2, initial=0, widget=forms.NumberInput(attrs={**FIELD_CLASSES, 'step': '0.01'}))
    deposit_paid   = forms.BooleanField(required=False, widget=forms.CheckboxInput(attrs={'class': 'custom-control-input'}))
    notes          = forms.CharField(required=False, widget=forms.Textarea(attrs={**FIELD_CLASSES, 'rows': 2}))

    def clean_cnic(self):
        raw = self.cleaned_data.get('cnic', '')
        try:
            cleaned = clean_cnic(raw)
        except ValueError as e:
            raise forms.ValidationError(str(e))
        if check_cnic_exists(cleaned):
            raise forms.ValidationError('A tenant with this CNIC is already registered.')
        return cleaned

    def clean(self):
        cleaned_data = super().clean()
        month_to_month = cleaned_data.get('month_to_month')
        end_date       = cleaned_data.get('end_date')
        start_date     = cleaned_data.get('start_date')
        if not month_to_month and not end_date:
            self.add_error('end_date', 'Provide an end date or check "Month to Month".')
        if start_date and end_date and end_date < start_date:
            self.add_error('end_date', 'End date must be after start date.')
        return cleaned_data

    def get_tenant_data(self) -> dict:
        d = self.cleaned_data
        return {
            'full_name':         d['full_name'],
            'email':             d['email'],
            'phone':             d['phone'],
            'cnic':              d['cnic'],
            'profession':        d.get('profession') or None,
            'emergency_contact': d.get('emergency_contact') or None,
            'id_document':       self.files.get('id_document'),
        }

    def get_lease_data(self) -> dict:
        d = self.cleaned_data
        return {
            'start_date':     d['start_date'],
            'end_date':       None if d.get('month_to_month') else d.get('end_date'),
            'monthly_rent':   d['monthly_rent'],
            'deposit_amount': d.get('deposit_amount', 0),
            'deposit_paid':   d.get('deposit_paid', False),
            'notes':          d.get('notes') or None,
        }


class TenantEditForm(forms.ModelForm):
    """Edit personal details only — not the lease."""
    class Meta:
        model = Tenant
        fields = ['full_name', 'email', 'phone', 'profession', 'emergency_contact', 'id_document']
        widgets = {
            'full_name':         forms.TextInput(attrs={**FIELD_CLASSES}),
            'email':             forms.EmailInput(attrs={**FIELD_CLASSES}),
            'phone':             forms.TextInput(attrs={**FIELD_CLASSES}),
            'profession':        forms.TextInput(attrs={**FIELD_CLASSES}),
            'emergency_contact': forms.TextInput(attrs={**FIELD_CLASSES}),
        }
