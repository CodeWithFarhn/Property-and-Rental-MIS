"""
finance/services.py
Business logic for invoicing and payments — atomic, formulaic.
"""
from decimal import Decimal
from datetime import datetime
from django.db import transaction
from django.utils import timezone


def generate_invoice_number() -> str:
    """
    Auto-generate invoice number: INV-YYYYMMDD-HHMMSS
    Adapted from reference code pattern. Guaranteed unique by timestamp
    + the UNIQUE constraint on Invoice.invoice_number.
    """
    now = datetime.now()
    return f"INV-{now.strftime('%Y%m%d')}-{now.strftime('%H%M%S')}"


@transaction.atomic
def create_invoice(lease, period_month, notes: str = '') -> 'Invoice':
    """
    Create a monthly invoice for a lease.
    - Checks for duplicate (lease + period_month) — raises if exists.
    - Auto-applies tenant account credit if available.
    - If credit fully covers the invoice, sets status=PAID immediately.

    period_month: date object representing the first day of the billing month.
    Returns: the created Invoice instance.
    """
    from finance.models import Invoice
    from tenants.models import Tenant

    # Duplicate check (also enforced at DB level by unique_together)
    if Invoice.objects.filter(lease=lease, period_month=period_month).exists():
        raise ValueError(
            f"Invoice already exists for lease #{lease.pk} "
            f"for {period_month.strftime('%B %Y')}."
        )

    # Calculate amount due — apply tenant credit balance if positive
    tenant = lease.tenant
    base_amount = lease.monthly_rent
    credit = max(Decimal('0.00'), tenant.account_balance)
    amount_due = max(Decimal('0.00'), base_amount - credit)

    # Due date: last day of the billing month
    import calendar
    last_day = calendar.monthrange(period_month.year, period_month.month)[1]
    due_date = period_month.replace(day=last_day)

    status = 'PAID' if amount_due == Decimal('0.00') else 'UNPAID'

    invoice = Invoice.objects.create(
        invoice_number=generate_invoice_number(),
        lease=lease,
        period_month=period_month,
        amount_due=amount_due,
        due_date=due_date,
        status=status,
        notes=notes or None,
    )

    # Deduct used credit from tenant's cached balance
    if credit > Decimal('0.00'):
        used_credit = min(credit, base_amount)
        tenant.account_balance -= used_credit
        tenant.save(update_fields=['account_balance', 'updated_at'])

    return invoice


@transaction.atomic
def record_payment(invoice_id: int, amount_paid: Decimal,
                   payment_method: str, date_paid,
                   recorded_by_id: int,
                   reference_code: str = '', notes: str = '') -> 'Payment':
    """
    Atomically:
      1. Creates a Payment record.
      2. Recalculates invoice status from the SUM of all payments.
      3. Updates tenant.account_balance cache.

    If overpaid, the excess becomes a credit on tenant.account_balance.
    """
    from finance.models import Invoice, Payment
    from django.db.models import Sum

    invoice = Invoice.objects.select_for_update().get(pk=invoice_id)

    payment = Payment.objects.create(
        invoice=invoice,
        amount_paid=amount_paid,
        payment_method=payment_method,
        reference_code=reference_code or None,
        recorded_by_id=recorded_by_id,
        date_paid=date_paid,
        notes=notes or None,
    )

    # Recalculate invoice status from DB aggregate (not in-memory)
    total_paid = (
        Payment.objects.filter(invoice=invoice)
        .aggregate(total=Sum('amount_paid'))['total']
        or Decimal('0.00')
    )

    if total_paid >= invoice.amount_due:
        invoice.status = 'PAID'
    elif total_paid > Decimal('0.00'):
        invoice.status = 'PARTIAL'
    else:
        invoice.status = 'UNPAID'

    invoice.save(update_fields=['status', 'updated_at'])

    # Update tenant.account_balance cache
    # Overpayment becomes credit (positive); underpayment leaves debt (negative)
    overpayment = total_paid - invoice.amount_due
    tenant = invoice.lease.tenant
    tenant.account_balance = overpayment  # will be negative if still owing on this invoice
    tenant.save(update_fields=['account_balance', 'updated_at'])

    return payment
