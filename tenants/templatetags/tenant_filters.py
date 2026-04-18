"""
tenants/templatetags/tenant_filters.py
Custom template filters for tenant-related display.
"""
from django import template
import re

register = template.Library()


@register.filter
def cnic_display(value):
    """
    Format a 13-digit raw CNIC string as XXXXX-XXXXXXX-X.
    DB always stores raw 13 digits (no dashes). This filter
    is the ONLY place dashes are added — for display only.
    """
    if not value:
        return value
    raw = re.sub(r'[\s\-]', '', str(value))
    if len(raw) == 13 and raw.isdigit():
        return f"{raw[:5]}-{raw[5:12]}-{raw[12]}"
    return value


@register.filter
def balance_class(value):
    """Returns Bootstrap text colour class based on balance sign."""
    try:
        v = float(value)
        if v > 0:
            return 'text-danger font-weight-bold'   # debt — owes money
        elif v < 0:
            return 'text-success font-weight-bold'  # credit — overpaid
        return 'text-muted'
    except (TypeError, ValueError):
        return ''


@register.filter
def pkr(value):
    """Format a number as PKR currency string."""
    try:
        return f"PKR {float(value):,.2f}"
    except (TypeError, ValueError):
        return value
