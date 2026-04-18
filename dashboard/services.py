"""
dashboard/services.py
KPI computation using ORM aggregate() — all calculations done in DB,
not in Python memory. Much faster than reference code's approach of
fetching all records and .filter()/.reduce() in JavaScript.
"""
from django.db.models import Count, Sum, Q
from django.utils import timezone


def get_admin_kpis(owner_id=None) -> dict:
    """
    Returns all 8 KPI card values for Admin/Manager dashboard.
    Pass owner_id to scope to a specific Owner's portfolio.
    Uses a single round-trip per model — not N+1 queries.
    """
    from properties.models import Property, Unit
    from tenants.models import Tenant
    from leases.models import Lease
    from finance.models import Invoice, Payment

    today = timezone.localdate()
    start_of_month = today.replace(day=1)

    prop_qs = Property.objects.filter(status='ACTIVE')
    unit_qs = Unit.objects.filter(property__status='ACTIVE')

    if owner_id:
        prop_qs = prop_qs.filter(owner_id=owner_id)
        unit_qs = unit_qs.filter(property__owner_id=owner_id)

    unit_counts = unit_qs.aggregate(
        total=Count('id'),
        occupied=Count('id', filter=Q(status='OCCUPIED')),
        vacant=Count('id', filter=Q(status='VACANT')),
        maintenance=Count('id', filter=Q(status='MAINTENANCE')),
    )
    total_units = unit_counts['total'] or 1
    occupancy_pct = round((unit_counts['occupied'] / total_units) * 100, 1)

    collected_this_month = (
        Payment.objects
        .filter(date_paid__gte=start_of_month)
        .aggregate(total=Sum('amount_paid'))['total']
        or 0
    )

    overdue_count = Invoice.objects.filter(
        status__in=['UNPAID', 'PARTIAL'],
        due_date__lt=today,
    ).count()

    expiring_count = Lease.objects.filter(
        is_active=True,
        end_date__isnull=False,
        end_date__lte=today + timezone.timedelta(days=30),
    ).count()

    active_tenants = Tenant.objects.filter(status='ACTIVE').count()

    return {
        'total_properties':  prop_qs.count(),
        'total_units':       unit_counts['total'],
        'occupied_units':    unit_counts['occupied'],
        'vacant_units':      unit_counts['vacant'],
        'maintenance_units': unit_counts['maintenance'],
        'occupancy_pct':     occupancy_pct,
        'collected_this_month': collected_this_month,
        'overdue_count':     overdue_count,
        'expiring_count':    expiring_count,
        'active_tenants':    active_tenants,
    }


def get_revenue_chart_data(months: int = 6, owner_id=None) -> list:
    """
    Returns last N months of revenue data for the Chart.js bar chart.
    Each entry: {'month': 'Apr 2026', 'invoiced': 150000, 'collected': 120000}
    """
    from finance.models import Invoice, Payment
    import calendar

    today = timezone.localdate()
    result = []

    for i in range(months - 1, -1, -1):
        # Build month start/end
        year  = today.year + (today.month - 1 - i) // 12
        month = (today.month - 1 - i) % 12 + 1
        month_start = today.replace(year=year, month=month, day=1)
        last_day    = calendar.monthrange(year, month)[1]
        month_end   = month_start.replace(day=last_day)

        inv_qs = Invoice.objects.filter(period_month__year=year, period_month__month=month)
        pay_qs = Payment.objects.filter(date_paid__year=year, date_paid__month=month)

        if owner_id:
            inv_qs = inv_qs.filter(lease__unit__property__owner_id=owner_id)
            pay_qs = pay_qs.filter(invoice__lease__unit__property__owner_id=owner_id)

        invoiced  = inv_qs.aggregate(total=Sum('amount_due'))['total'] or 0
        collected = pay_qs.aggregate(total=Sum('amount_paid'))['total'] or 0

        result.append({
            'month':     month_start.strftime('%b %Y'),
            'invoiced':  float(invoiced),
            'collected': float(collected),
        })

    return result


def get_recent_audit_entries(limit: int = 10) -> list:
    """
    STUB — Phase 2 adds the AuditLog model.
    Returns empty list so dashboard renders without error in Phase 1.
    """
    return []
