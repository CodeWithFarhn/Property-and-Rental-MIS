from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db.models import Q
from properties.models import Property

class Service(models.Model):
    """Available services that can be included in a contract (e.g. Tenant Mgmt, Maintenance)."""
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name

class OwnerContract(models.Model):
    """The commercial agreement between the management company and an owner."""
    STATUS_CHOICES = [
        ('DRAFT', 'Draft'),
        ('ACTIVE', 'Active'),
        ('TERMINATED', 'Terminated'),
    ]

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.RESTRICT,
        related_name='contracts',
        limit_choices_to={'role': 'OWNER'}
    )
    package_name = models.CharField(max_length=200, blank=True, null=True, help_text="Optional package name (e.g., 'Premium', 'Standard')")
    commission_rate = models.DecimalField(max_digits=5, decimal_places=2, help_text="Percentage e.g. 7.50")
    start_date = models.DateField()
    end_date = models.DateField(blank=True, null=True, help_text="Leave blank for rolling contract")
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='DRAFT')
    agreement_document = models.FileField(upload_to='documents/contracts/', blank=True, null=True)
    tc_version = models.CharField(max_length=50, blank=True, null=True)
    tc_signed_date = models.DateField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        package_text = f" - {self.package_name}" if self.package_name else ""
        return f"Contract {self.id} ({self.owner.display_name}){package_text}"

class ContractService(models.Model):
    """Junction mapping services to a contract."""
    contract = models.ForeignKey(OwnerContract, on_delete=models.CASCADE, related_name='contract_services')
    service = models.ForeignKey(Service, on_delete=models.RESTRICT, related_name='service_contracts')

    class Meta:
        unique_together = ('contract', 'service')

    def __str__(self):
        return f"{self.contract} -> {self.service}"

class ContractProperty(models.Model):
    """
    Junction mapping properties to a contract.
    Crucial Constraint: A single property cannot belong to multiple ACTIVE contracts with overlapping dates.
    """
    contract = models.ForeignKey(OwnerContract, on_delete=models.CASCADE, related_name='enrolled_properties')
    property = models.ForeignKey(Property, on_delete=models.RESTRICT, related_name='contract_enrollments')
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('contract', 'property')

    def clean(self):
        """Enforce that the property doesn't have another ACTIVE contract."""
        if self.contract.status == 'ACTIVE':
            overlapping_active = ContractProperty.objects.filter(
                property=self.property,
                contract__status='ACTIVE'
            ).exclude(pk=self.pk)
            if overlapping_active.exists():
                raise ValidationError("This property is already assigned to another ACTIVE contract.")

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.property.name} under {self.contract}"
