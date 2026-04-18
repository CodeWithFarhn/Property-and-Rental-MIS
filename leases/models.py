"""
leases/models.py
Lease model — one active lease per unit enforced by:
  1. DB triggers (RunSQL in migration 0002)
  2. Django application-layer check in leases/services.py
"""
from django.db import models


class Lease(models.Model):
    """Formal rental agreement between a Tenant and a Unit."""
    tenant         = models.ForeignKey('tenants.Tenant', on_delete=models.RESTRICT, related_name='leases')
    unit           = models.ForeignKey('properties.Unit', on_delete=models.RESTRICT, related_name='leases')
    start_date     = models.DateField()
    end_date       = models.DateField(null=True, blank=True, help_text='Leave blank for month-to-month.')
    monthly_rent   = models.DecimalField(max_digits=12, decimal_places=2)
    deposit_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    deposit_paid   = models.BooleanField(default=False)
    is_active      = models.BooleanField(default=True)
    notes          = models.TextField(blank=True, null=True)
    created_at     = models.DateTimeField(auto_now_add=True)
    updated_at     = models.DateTimeField(auto_now=True, null=True)

    class Meta:
        indexes = [
            models.Index(fields=['tenant'],              name='idx_lease_tenant'),
            models.Index(fields=['unit'],                name='idx_lease_unit'),
            models.Index(fields=['is_active'],           name='idx_lease_is_active'),
            models.Index(fields=['unit', 'is_active'],   name='idx_lease_unit_active'),
        ]

    def __str__(self):
        status = 'Active' if self.is_active else 'Terminated'
        return f"Lease #{self.pk} — {self.tenant} @ {self.unit} [{status}]"

    @property
    def is_month_to_month(self):
        return self.end_date is None

    def clean(self):
        """Application-layer check for one active lease per unit."""
        from django.core.exceptions import ValidationError
        if self.is_active:
            qs = Lease.objects.filter(unit=self.unit, is_active=True)
            if self.pk:
                qs = qs.exclude(pk=self.pk)
            if qs.exists():
                raise ValidationError(
                    'This unit already has an active lease. '
                    'Terminate the existing lease before creating a new one.'
                )
        if self.end_date and self.start_date and self.end_date < self.start_date:
            raise ValidationError('End date must be on or after start date.')
