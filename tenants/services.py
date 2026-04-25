"""
tenants/services.py
Core business logic:
  - CNIC validation and display
  - Outstanding balance formula B = (P × M) − ΣR
  - admit_tenant()     — atomic: Tenant + Lease + Unit status
  - terminate_tenant() — atomic: INACTIVE + lease close + VACANT
"""
import re
from decimal import Decimal
from django.db import transaction
from django.utils import timezone


# ── CNIC Utilities ────────────────────────────────────────────────────────────

def clean_cnic(raw_input: str) -> str:
    """
    Strip dashes/spaces from CNIC input and validate it is 13 digits.
    DB always stores 13 raw digits — never dashes.
    Raises ValueError if invalid.
    """
    cleaned = re.sub(r'[\s\-]', '', str(raw_input))
    if not cleaned.isdigit() or len(cleaned) != 13:
        raise ValueError('CNIC must be exactly 13 digits.')
    return cleaned


def check_cnic_exists(cnic: str, exclude_id: int = None) -> bool:
    """Return True if a tenant with this CNIC already exists."""
    from tenants.models import Tenant
    qs = Tenant.objects.filter(cnic=cnic)
    if exclude_id:
        qs = qs.exclude(pk=exclude_id)
    return qs.exists()


# ── Balance Formula ───────────────────────────────────────────────────────────

def calculate_outstanding_balance(tenant) -> Decimal:
    """
    B = ΣInvoices(amount_due) − ΣPayments(amount_paid)
    The sum of all invoice amounts minus the sum of all payments made.
    """
    from django.db.models import Sum
    from finance.models import Invoice, Payment

    total_invoiced = Invoice.objects.filter(lease__tenant=tenant).aggregate(
        total=Sum('amount_due')
    )['total'] or Decimal('0.00')

    total_paid = Payment.objects.filter(invoice__lease__tenant=tenant).aggregate(
        total=Sum('amount_paid')
    )['total'] or Decimal('0.00')

    balance = total_invoiced - total_paid

    # Update the cached field on the tenant
    tenant.account_balance = balance
    tenant.save(update_fields=['account_balance', 'updated_at'])

    return balance


# ── Atomic Operations ──────────────────────────────────────────────────────────

@transaction.atomic
def admit_tenant(tenant_data: dict, lease_data: dict, unit_id: int):
    """
    Atomically creates:
      1. Tenant record
      2. Lease record
      3. Updates Unit.status → OCCUPIED
    Full rollback on any failure (including DB trigger violations).

    tenant_data: dict of Tenant field values (cnic already cleaned)
    lease_data:  dict of Lease field values (excluding tenant/unit)
    unit_id:     PK of the unit to assign

    Returns: the created Tenant instance.
    """
    from tenants.models import Tenant
    from leases.models import Lease
    from properties.models import Unit

    # Lock the unit row to prevent race conditions
    unit = Unit.objects.select_for_update().get(pk=unit_id)
    if unit.status != 'VACANT':
        raise ValueError(f"Unit '{unit.unit_number}' is no longer available (status: {unit.status}).")

    # 1. Create tenant
    tenant = Tenant.objects.create(**tenant_data)

    # 2. Create lease (DB trigger will fire and validate)
    Lease.objects.create(tenant=tenant, unit=unit, **lease_data)

    # 3. Mark unit as OCCUPIED
    unit.status = 'OCCUPIED'
    unit.save(update_fields=['status', 'updated_at'])

    return tenant


@transaction.atomic
def terminate_tenant(tenant_id: int, termination_date=None):
    """
    Atomically:
      1. Sets tenant.status = INACTIVE
      2. Closes the active lease (is_active=False, end_date=termination_date)
      3. Reverts unit.status = VACANT

    All payment/invoice history is preserved (RESTRICT FK on delete).
    termination_date defaults to today if not provided.
    """
    from tenants.models import Tenant
    from leases.models import Lease
    from properties.models import Unit

    if termination_date is None:
        termination_date = timezone.localdate()

    tenant = Tenant.objects.select_for_update().get(pk=tenant_id)
    active_lease = Lease.objects.select_for_update().filter(
        tenant=tenant, is_active=True
    ).first()

    if active_lease:
        unit = Unit.objects.select_for_update().get(pk=active_lease.unit_id)
        active_lease.is_active = False
        active_lease.end_date = termination_date
        active_lease.save(update_fields=['is_active', 'end_date', 'updated_at'])
        unit.status = 'VACANT'
        unit.save(update_fields=['status', 'updated_at'])

    tenant.status = 'INACTIVE'
    tenant.save(update_fields=['status', 'updated_at'])
