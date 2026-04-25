from django import forms
from .models import MaintenanceTicket

class MaintenanceTicketForm(forms.ModelForm):
    class Meta:
        model = MaintenanceTicket
        fields = ['unit', 'title', 'description', 'urgency', 'assigned_to']
        widgets = {
            'unit': forms.Select(attrs={'class': 'form-control select2'}),
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Brief description of issue'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'urgency': forms.Select(attrs={'class': 'form-control'}),
            'assigned_to': forms.Select(attrs={'class': 'form-control select2'}),
        }

    def clean_unit(self):
        unit = self.cleaned_data.get('unit')
        if unit:
            # Check if property has an active contract with the 'maintenance' service
            has_maintenance = unit.property.contract_enrollments.filter(
                contract__status='ACTIVE',
                contract__contract_services__service__slug='maintenance'
            ).exists()
            if not has_maintenance:
                raise forms.ValidationError("The contract for this property does not include maintenance services.")
        return unit

class TicketStatusUpdateForm(forms.ModelForm):
    notes = forms.CharField(widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3}), required=False, help_text="Add a note to the timeline")
    
    class Meta:
        model = MaintenanceTicket
        fields = ['status', 'cost', 'cost_document']
        widgets = {
            'status': forms.Select(attrs={'class': 'form-control'}),
            'cost': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'cost_document': forms.FileInput(attrs={'class': 'form-control'}),
        }
