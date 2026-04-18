"""
properties/models.py
Location, Property, Unit models.
"""
from django.db import models
from django.conf import settings


class Location(models.Model):
    """Standardised area/neighbourhood lookup — prevents free-text typos."""
    name = models.CharField(max_length=100, unique=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class Property(models.Model):
    """A building or address containing one or more units."""
    STATUS_CHOICES = [('ACTIVE', 'Active'), ('ARCHIVED', 'Archived')]

    name       = models.CharField(max_length=200)
    address    = models.TextField()
    location   = models.ForeignKey(Location, on_delete=models.RESTRICT, related_name='properties')
    owner      = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.RESTRICT,
        related_name='owned_properties',
        limit_choices_to={'role': 'OWNER'},
    )
    status     = models.CharField(max_length=10, choices=STATUS_CHOICES, default='ACTIVE')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True, null=True)

    class Meta:
        verbose_name_plural = 'properties'
        indexes = [
            models.Index(fields=['owner'],    name='idx_property_owner'),
            models.Index(fields=['location'], name='idx_property_location'),
            models.Index(fields=['status'],   name='idx_property_status'),
        ]

    def __str__(self):
        return self.name


class Unit(models.Model):
    """A single rentable space within a Property."""
    TYPE_CHOICES = [
        ('APARTMENT', 'Apartment'), ('SHOP', 'Shop'),
        ('STUDIO', 'Studio'),       ('HOUSE', 'House'),
        ('OTHER', 'Other'),
    ]
    STATUS_CHOICES = [
        ('VACANT',      'Vacant'),
        ('OCCUPIED',    'Occupied'),
        ('MAINTENANCE', 'Under Maintenance'),
    ]

    property     = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='units')
    unit_number  = models.CharField(max_length=50)
    unit_type    = models.CharField(max_length=20, choices=TYPE_CHOICES, default='APARTMENT')
    bedrooms     = models.PositiveIntegerField(default=0)
    monthly_rent = models.DecimalField(max_digits=12, decimal_places=2)
    status       = models.CharField(max_length=15, choices=STATUS_CHOICES, default='VACANT')
    updated_at   = models.DateTimeField(auto_now=True, null=True)

    class Meta:
        unique_together = [('property', 'unit_number')]
        indexes = [
            models.Index(fields=['property'], name='idx_unit_property'),
            models.Index(fields=['status'],   name='idx_unit_status'),
        ]

    def __str__(self):
        return f"{self.property.name} — {self.unit_number}"
