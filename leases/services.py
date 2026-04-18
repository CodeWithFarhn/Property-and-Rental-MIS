"""
leases/services.py
Business logic for lease management.
"""
from django.utils import timezone


def get_active_lease(tenant_id):
    """Return the currently active lease for a tenant, or None."""
    from leases.models import Lease
    return Lease.objects.filter(tenant_id=tenant_id, is_active=True).select_related('unit__property').first()


def get_expiring_leases(days: int = 30):
    """
    Return queryset of active leases whose end_date falls within
    the next `days` days. Excludes month-to-month (end_date=None).
    """
    from leases.models import Lease
    today = timezone.localdate()
    cutoff = today + timezone.timedelta(days=days)
    return (
        Lease.objects
        .filter(is_active=True, end_date__isnull=False, end_date__lte=cutoff)
        .select_related('tenant', 'unit__property')
        .order_by('end_date')
    )


def renew_lease(lease_id: int, new_end_date, new_monthly_rent=None, notes: str = ''):
    """
    STUB — Phase 3 feature.
    Terminates the current lease and creates a new one for the same
    tenant+unit with an updated end_date and (optionally) a new rent.
    Full lease history is preserved.
    """
    raise NotImplementedError(
        'Lease renewal is a Phase 3 feature. '
        'This stub exists so models are stable from Phase 1.'
    )
