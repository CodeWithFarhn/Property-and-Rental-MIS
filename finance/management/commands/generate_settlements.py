import datetime
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db.models import Sum
from finance.models import MonthlySettlement, Payment
from contracts.models import ContractProperty, OwnerContract
from maintenance.models import MaintenanceTicket

class Command(BaseCommand):
    help = 'Generate monthly settlements for active contracts'

    def add_arguments(self, parser):
        parser.add_argument(
            '--month',
            type=str,
            help='Specify month in YYYY-MM format to generate settlements for a specific month instead of the previous month.'
        )

    def handle(self, *args, **kwargs):
        month_str = kwargs['month']
        
        if month_str:
            try:
                y, m = map(int, month_str.split('-'))
                period_month = datetime.date(y, m, 1)
            except ValueError:
                self.stderr.write(self.style.ERROR("Invalid format for --month. Use YYYY-MM."))
                return
        else:
            today = timezone.localdate()
            first_of_this_month = today.replace(day=1)
            last_month = first_of_this_month - datetime.timedelta(days=1)
            period_month = last_month.replace(day=1)

        active_enrollments = ContractProperty.objects.filter(contract__status='ACTIVE')
        
        count = 0
        for enrollment in active_enrollments:
            contract = enrollment.contract
            property_obj = enrollment.property

            # gross rent: sum of payments for this property in the period
            payments = Payment.objects.filter(
                invoice__lease__unit__property=property_obj,
                date_paid__year=period_month.year,
                date_paid__month=period_month.month
            )
            gross_rent = payments.aggregate(t=Sum('amount_paid'))['t'] or Decimal('0.00')

            # maintenance: sum of resolved tickets cost in the period for this property
            tickets = MaintenanceTicket.objects.filter(
                unit__property=property_obj,
                status__in=['RESOLVED', 'CLOSED'],
                resolved_at__year=period_month.year,
                resolved_at__month=period_month.month
            )
            maint_cost = tickets.aggregate(t=Sum('cost'))['t'] or Decimal('0.00')

            commission = (gross_rent * contract.commission_rate) / Decimal('100.00')
            net = gross_rent - commission - maint_cost

            settlement, created = MonthlySettlement.objects.get_or_create(
                contract=contract,
                property=property_obj,
                period_month=period_month,
                defaults={
                    'gross_rent_collected': gross_rent,
                    'commission_deducted': commission,
                    'maintenance_costs': maint_cost,
                    'net_remittance': net,
                    'status': 'PENDING'
                }
            )
            
            if created:
                count += 1
                self.stdout.write(self.style.SUCCESS(f"Created settlement for {contract} - {property_obj} ({period_month.strftime('%Y-%m')})"))

        self.stdout.write(self.style.SUCCESS(f"Successfully generated {count} new settlements for {period_month.strftime('%B %Y')}."))
