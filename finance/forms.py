"""
finance/forms.py
"""
from django import forms
from django.utils import timezone
from finance.models import Invoice, Payment
from leases.models import Lease
from tenants.models import Tenant

FIELD_CLASSES = {'class': 'form-control'}


class InvoiceForm(forms.Form):
    lease = forms.ModelChoiceField(
        queryset=Lease.objects.filter(is_active=True).select_related('tenant', 'unit'),
        empty_label='— Select Lease / Tenant —',
        widget=forms.Select(attrs={**FIELD_CLASSES}),
    )
    period_month = forms.DateField(
        widget=forms.DateInput(attrs={**FIELD_CLASSES, 'type': 'month'}),
        input_formats=['%Y-%m'],
        help_text='Select the billing month.',
    )
    notes = forms.CharField(required=False, widget=forms.Textarea(attrs={**FIELD_CLASSES, 'rows': 2}))

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        # Owner sees only their own property leases
        if user and user.role == 'OWNER':
            self.fields['lease'].queryset = Lease.objects.filter(
                is_active=True, unit__property__owner=user
            ).select_related('tenant', 'unit')

    def clean_period_month(self):
        """Ensure period_month is the first day of the month."""
        d = self.cleaned_data.get('period_month')
        if d:
            return d.replace(day=1)
        return d


class PaymentForm(forms.Form):
    invoice = forms.ModelChoiceField(
        queryset=Invoice.objects.filter(status__in=['UNPAID', 'PARTIAL']).select_related('lease__tenant'),
        empty_label='— Select Invoice —',
        widget=forms.Select(attrs={**FIELD_CLASSES}),
    )
    amount_paid    = forms.DecimalField(max_digits=12, decimal_places=2,
                                        widget=forms.NumberInput(attrs={**FIELD_CLASSES, 'step': '0.01'}))
    payment_method = forms.ChoiceField(choices=Payment.METHOD_CHOICES,
                                       widget=forms.Select(attrs={**FIELD_CLASSES}))
    reference_code = forms.CharField(max_length=100, required=False,
                                     widget=forms.TextInput(attrs={**FIELD_CLASSES, 'placeholder': 'Transaction ID / receipt no.'}))
    date_paid      = forms.DateField(initial=timezone.localdate,
                                     widget=forms.DateInput(attrs={**FIELD_CLASSES, 'type': 'date'}))
    notes          = forms.CharField(required=False, widget=forms.Textarea(attrs={**FIELD_CLASSES, 'rows': 2}))

    def __init__(self, *args, tenant_id=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tenant_id:
            self.fields['invoice'].queryset = self.fields['invoice'].queryset.filter(lease__tenant_id=tenant_id)

    def clean_amount_paid(self):
        amount = self.cleaned_data.get('amount_paid')
        if amount is not None and amount <= 0:
            raise forms.ValidationError('Amount must be greater than zero.')
        return amount
