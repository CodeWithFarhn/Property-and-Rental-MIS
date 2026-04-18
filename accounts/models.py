from django.contrib.auth.models import AbstractUser
from django.db import models


class CustomUser(AbstractUser):
    """
    Central auth model. Role field drives all RBAC logic.
    Password is bcrypt-hashed by Django automatically.
    """
    ROLE_CHOICES = [
        ('ADMIN',   'Admin'),
        ('MANAGER', 'Property Manager'),
        ('STAFF',   'Staff / Caretaker'),
        ('OWNER',   'Property Owner'),
        ('TENANT',  'Tenant'),
    ]

    full_name = models.CharField(max_length=200, blank=True, default='')
    phone     = models.CharField(max_length=20, blank=True, null=True)
    role      = models.CharField(max_length=20, choices=ROLE_CHOICES, default='TENANT')

    class Meta:
        indexes = [
            models.Index(fields=['role'], name='idx_user_role'),
        ]

    def __str__(self):
        return f"{self.get_full_name() or self.username} ({self.role})"

    @property
    def display_name(self):
        return self.full_name or self.get_full_name() or self.username

    def is_admin_or_manager(self):
        return self.role in ('ADMIN', 'MANAGER')
