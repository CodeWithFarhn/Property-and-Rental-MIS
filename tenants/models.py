"""
tenants/models.py
Tenant model — soft-delete via status=INACTIVE, never hard-deleted.
"""
from django.db import models
from django.conf import settings


class Tenant(models.Model):
    """
    Core tenant record.
    account_balance: cached running credit/debit.
      Positive  = credit (tenant has overpaid, applied to next invoice)
      Negative  = debt   (tenant has outstanding balance)
    Source of truth is B=(P×M)−ΣR formula; this field is kept in sync
    for fast UI lookups only.
    """
    STATUS_CHOICES = [('ACTIVE', 'Active'), ('INACTIVE', 'Inactive')]

    user              = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='tenant_profile',
    )
    full_name         = models.CharField(max_length=200)
    email             = models.EmailField()
    phone             = models.CharField(max_length=20)
    cnic              = models.CharField(
        max_length=13, unique=True,
        help_text='13 raw digits, no dashes. Display formatting applied in templates.'
    )
    profession        = models.CharField(max_length=100, blank=True, null=True)
    emergency_contact = models.CharField(max_length=200, blank=True, null=True)
    account_balance   = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    status            = models.CharField(max_length=10, choices=STATUS_CHOICES, default='ACTIVE')
    id_document       = models.FileField(upload_to='tenant_docs/', blank=True, null=True)
    created_at        = models.DateTimeField(auto_now_add=True)
    updated_at        = models.DateTimeField(auto_now=True, null=True)

    class Meta:
        indexes = [
            models.Index(fields=['status'], name='idx_tenant_status'),
            models.Index(fields=['cnic'],   name='idx_tenant_cnic'),
        ]

    def __str__(self):
        return self.full_name
