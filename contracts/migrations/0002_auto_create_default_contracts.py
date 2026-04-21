from django.db import migrations
from django.utils import timezone

def create_default_contracts(apps, schema_editor):
    Property = apps.get_model('properties', 'Property')
    OwnerContract = apps.get_model('contracts', 'OwnerContract')
    ContractProperty = apps.get_model('contracts', 'ContractProperty')
    ContractService = apps.get_model('contracts', 'ContractService')
    Service = apps.get_model('contracts', 'Service')
    
    # Ensure basic service exists
    service, _ = Service.objects.get_or_create(
        slug='tenant-management',
        defaults={'name': 'Tenant Management', 'description': 'Basic tenant management'}
    )
    
    # Get all owners who have properties
    owners = set(Property.objects.values_list('owner_id', flat=True))
    today = timezone.now().date()
    
    for owner_id in owners:
        # Check if they already have an active contract to avoid duplicates if run multiple times
        if OwnerContract.objects.filter(owner_id=owner_id, status='ACTIVE').exists():
            continue

        # Create an active contract for this owner
        contract = OwnerContract.objects.create(
            owner_id=owner_id,
            label='Legacy System Default',
            commission_rate=5.00,
            start_date=today,
            status='ACTIVE'
        )
        
        # Link service
        ContractService.objects.create(contract=contract, service=service)
        
        # Link properties
        owner_properties = Property.objects.filter(owner_id=owner_id)
        for prop in owner_properties:
            ContractProperty.objects.create(contract=contract, property=prop)

class Migration(migrations.Migration):

    dependencies = [
        ('contracts', '0001_initial'),
        ('properties', '0001_initial'), # Assume properties app already exists and migrated
    ]

    operations = [
        migrations.RunPython(create_default_contracts, reverse_code=migrations.RunPython.noop),
    ]
