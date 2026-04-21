"""
finance/models.py
Invoice and Payment models.
"""
from django.db import models
from django.conf import settings


class Invoice(models.Model):
    """
    One invoice per active lease per calendar month.
    UNIQUE(lease, period_month) prevents duplicate billing.
    """
    STATUS_CHOICES = [
        ('UNPAID',  'Unpaid'),
        ('PARTIAL', 'Partial'),
        ('PAID',    'Paid'),
    ]

    invoice_number = models.CharField(max_length=30, unique=True)
    lease          = models.ForeignKey('leases.Lease', on_delete=models.RESTRICT, related_name='invoices')
    period_month   = models.DateField(help_text='First day of the billing month.')
    amount_due     = models.DecimalField(max_digits=12, decimal_places=2)
    due_date       = models.DateField()
    status         = models.CharField(max_length=10, choices=STATUS_CHOICES, default='UNPAID')
    notes          = models.TextField(blank=True, null=True)
    created_at     = models.DateTimeField(auto_now_add=True)
    updated_at     = models.DateTimeField(auto_now=True, null=True)

    class Meta:
        unique_together = [('lease', 'period_month')]
        indexes = [
            models.Index(fields=['lease'],        name='idx_invoice_lease'),
            models.Index(fields=['status'],       name='idx_invoice_status'),
            models.Index(fields=['period_month'], name='idx_invoice_period'),
        ]

    def __str__(self):
        return f"{self.invoice_number} [{self.status}]"

    @property
    def total_paid(self):
        from django.db.models import Sum
        result = self.payments.aggregate(total=Sum('amount_paid'))['total']
        return result or 0

    @property
    def remaining_balance(self):
        return self.amount_due - self.total_paid


class Payment(models.Model):
    """A single payment transaction against an invoice."""
    METHOD_CHOICES = [
        ('CASH',          'Cash'),
        ('BANK_TRANSFER', 'Bank Transfer'),
        ('EASYPAISA',     'EasyPaisa'),
        ('JAZZCASH',      'JazzCash'),
        ('CHEQUE',        'Cheque'),
    ]

    invoice        = models.ForeignKey(Invoice, on_delete=models.RESTRICT, related_name='payments')
    amount_paid    = models.DecimalField(max_digits=12, decimal_places=2)
    payment_method = models.CharField(max_length=15, choices=METHOD_CHOICES, default='CASH')
    reference_code = models.CharField(max_length=100, blank=True, null=True)
    recorded_by    = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.RESTRICT, related_name='recorded_payments'
    )
    date_paid      = models.DateField()
    proof_document = models.FileField(upload_to='documents/payments/', blank=True, null=True)
    notes          = models.TextField(blank=True, null=True)
    created_at     = models.DateTimeField(auto_now_add=True)
    updated_at     = models.DateTimeField(auto_now=True, null=True)

    class Meta:
        indexes = [
            models.Index(fields=['invoice'],  name='idx_payment_invoice'),
            models.Index(fields=['date_paid'], name='idx_payment_date'),
        ]

    def __str__(self):
        return f"Payment PKR {self.amount_paid} on {self.date_paid} for {self.invoice.invoice_number}"

class MonthlySettlement(models.Model):
    """
    Computed financial outcome for an owner contract per billing cycle.
    This is the financial truth for owner payouts.
    """
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('REMITTED', 'Remitted'),
    ]

    contract = models.ForeignKey('contracts.OwnerContract', on_delete=models.RESTRICT, related_name='settlements')
    property = models.ForeignKey('properties.Property', on_delete=models.RESTRICT, related_name='settlements')
    period_month = models.DateField(help_text="First day of the settlement month")
    
    gross_rent_collected = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    commission_deducted = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    maintenance_costs = models.DecimalField(max_digits=12, decimal_places=2, default=0, help_text="Sum of resolved tickets within period")
    net_remittance = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='PENDING')
    remittance_proof = models.FileField(upload_to='documents/settlements/', blank=True, null=True)
    remitted_at = models.DateTimeField(blank=True, null=True)
    
    generated_at = models.DateTimeField(auto_now_add=True)
    calculation_snapshot = models.JSONField(blank=True, null=True, help_text="Preserves historical truth of calculations")

    class Meta:
        unique_together = ('contract', 'property', 'period_month')
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['period_month']),
        ]

    def __str__(self):
        return f"Settlement {self.period_month.strftime('%b %Y')} for {self.contract}"
