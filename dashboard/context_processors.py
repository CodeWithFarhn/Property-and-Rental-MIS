"""
dashboard/context_processors.py
STUB — Phase 2 adds the SystemSettings model with logo, org name, etc.
Returns hard-coded values so all templates have these variables available.
"""


def system_settings(request):
    """
    Injects org_name and currency_symbol into every template context.
    Phase 2 replaces the hard-coded values with DB-loaded SystemSettings.
    """
    return {
        'org_name':        'Rental Property MIS',
        'currency_symbol': 'PKR',
        'org_contact_email': '',
        'org_logo': None,
    }
