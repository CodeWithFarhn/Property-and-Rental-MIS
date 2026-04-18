"""
properties/services.py
Business logic for properties and units — pure Python, no HTTP.
"""
from django.db.models import Count, Q


def get_vacant_units(property_id=None):
    """Return queryset of VACANT units, optionally filtered by property."""
    from properties.models import Unit
    qs = Unit.objects.filter(status='VACANT').select_related('property')
    if property_id:
        qs = qs.filter(property_id=property_id)
    return qs


def get_property_occupancy(property_id):
    """
    Return a dict with occupancy counts for a single property.
    Uses DB aggregation — no Python-side counting.
    """
    from properties.models import Unit
    result = Unit.objects.filter(property_id=property_id).aggregate(
        total=Count('id'),
        occupied=Count('id', filter=Q(status='OCCUPIED')),
        vacant=Count('id', filter=Q(status='VACANT')),
        maintenance=Count('id', filter=Q(status='MAINTENANCE')),
    )
    total = result['total'] or 1  # avoid ZeroDivisionError
    result['occupancy_pct'] = round((result['occupied'] / total) * 100, 1)
    return result


def get_all_properties_occupancy():
    """Return occupancy data for all ACTIVE properties (used by dashboard)."""
    from properties.models import Property
    properties = Property.objects.filter(status='ACTIVE').prefetch_related('units')
    data = []
    for prop in properties:
        occ = get_property_occupancy(prop.id)
        occ['property'] = prop
        data.append(occ)
    return data


def get_units_for_dropdown(property_id):
    """Return VACANT units for a given property — used by HTMX cascade on Add Tenant form."""
    from properties.models import Unit
    return Unit.objects.filter(
        property_id=property_id, status='VACANT'
    ).values('id', 'unit_number', 'unit_type', 'monthly_rent')


def get_unit_info(unit_id):
    """Return unit details for the Add Tenant info box."""
    from properties.models import Unit
    from django.utils import timezone

    try:
        unit = Unit.objects.select_related('property').get(id=unit_id)
    except Unit.DoesNotExist:
        return None
    return {
        'unit': unit,
        'monthly_rent': unit.monthly_rent,
        'status': unit.status,
    }


def archive_property(property_id):
    """Soft-archive a property — hides from active lists, preserves history."""
    from properties.models import Property
    Property.objects.filter(pk=property_id).update(status='ARCHIVED')
