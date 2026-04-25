"""dashboard/views.py"""
import json
from django.shortcuts import render, redirect
from django.views import View
from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required

from accounts.decorators import role_required
from dashboard import services
from leases.services import get_expiring_leases
from finance.models import Payment, Invoice
from tenants.models import Tenant
from django.db.models import Sum


@method_decorator(login_required, name='dispatch')
@method_decorator(role_required('ADMIN', 'MANAGER'), name='dispatch')
class AdminManagerDashboardView(View):
    def get(self, request):
        kpis = services.get_admin_kpis()
        expiring = get_expiring_leases(days=30)
        audit_entries = services.get_recent_audit_entries()
        
        # Check if invoices for the current month have been generated
        from leases.models import Lease
        from django.utils import timezone
        
        today = timezone.localdate()
        current_month = today.replace(day=1)
        needs_invoicing = False
        
        if Lease.objects.filter(is_active=True).exists() and not Invoice.objects.filter(period_month=current_month).exists():
            needs_invoicing = True
            
        return render(request, 'dashboard/admin_dashboard.html', {
            'kpis': kpis,
            'expiring_leases': expiring,
            'audit_entries': audit_entries,
            'needs_invoicing': needs_invoicing,
        })


@method_decorator(login_required, name='dispatch')
@method_decorator(role_required('OWNER'), name='dispatch')
class OwnerDashboardView(View):
    def get(self, request):
        kpis = services.get_admin_kpis(owner_id=request.user.id)
        expiring = get_expiring_leases(days=30)
        return render(request, 'dashboard/owner_dashboard.html', {
            'kpis': kpis,
            'expiring_leases': expiring,
        })


@method_decorator(login_required, name='dispatch')
@method_decorator(role_required('STAFF'), name='dispatch')
class StaffDashboardView(View):
    def get(self, request):
        from finance.models import Payment
        from django.utils import timezone
        today = timezone.localdate()
        payments_today = Payment.objects.filter(
            recorded_by=request.user, date_paid=today
        ).count()
        return render(request, 'dashboard/staff_dashboard.html', {
            'payments_today': payments_today,
        })


@method_decorator(login_required, name='dispatch')
@method_decorator(role_required('TENANT'), name='dispatch')
class TenantDashboardView(View):
    def get(self, request):
        try:
            tenant = request.user.tenant_profile
        except Exception:
            tenant = None
        return render(request, 'dashboard/tenant_dashboard.html', {'tenant': tenant})


@method_decorator(login_required, name='dispatch')
@method_decorator(role_required('ADMIN', 'MANAGER', 'OWNER'), name='dispatch')
class RevenueChartDataView(View):
    def get(self, request):
        owner_id = request.user.id if request.user.role == 'OWNER' else None
        data = services.get_revenue_chart_data(months=6, owner_id=owner_id)
        return JsonResponse(data, safe=False)


@method_decorator(login_required, name='dispatch')
class ExpiryPanelView(View):
    def get(self, request):
        expiring = get_expiring_leases(days=30)
        return render(request, 'dashboard/partials/expiry_panel.html', {
            'expiring_leases': expiring,
        })

@method_decorator(login_required, name='dispatch')
@method_decorator(role_required('ADMIN', 'MANAGER', 'OWNER'), name='dispatch')
class MonthlyPaymentsReportView(View):
    def get(self, request):
        month = request.GET.get('month')
        payments = Payment.objects.select_related('invoice__lease__tenant', 'invoice__lease__unit__property')
        
        if request.user.role == 'OWNER':
            payments = payments.filter(invoice__lease__unit__property__contract_enrollments__contract__owner=request.user, invoice__lease__unit__property__contract_enrollments__contract__status='ACTIVE')

        if month:
            # month format: YYYY-MM
            try:
                y, m = month.split('-')
                payments = payments.filter(date_paid__year=y, date_paid__month=m)
            except ValueError:
                pass
        else:
            now = timezone.now()
            payments = payments.filter(date_paid__year=now.year, date_paid__month=now.month)
            month = f"{now.year}-{now.month:02d}"

        payments = payments.order_by('-date_paid')
        total_collected = payments.aggregate(total=Sum('amount_paid'))['total'] or 0

        if request.headers.get('HX-Request'):
            return render(request, 'reports/partials/monthly_payments_table.html', {
                'payments': payments,
                'total_collected': total_collected,
            })
            
        return render(request, 'reports/monthly_payments.html', {
            'payments': payments,
            'total_collected': total_collected,
            'selected_month': month,
        })

@method_decorator(login_required, name='dispatch')
@method_decorator(role_required('ADMIN', 'MANAGER', 'OWNER'), name='dispatch')
class OutstandingBalancesReportView(View):
    def get(self, request):
        from tenants.services import calculate_outstanding_balance
        
        tenants = Tenant.objects.filter(status='ACTIVE')
        
        if request.user.role == 'OWNER':
            # Only tenants that have a lease in a property owned by this owner
            tenants = tenants.filter(leases__unit__property__contract_enrollments__contract__owner=request.user, leases__unit__property__contract_enrollments__contract__status='ACTIVE').distinct()

        tenant_balances = []
        total_outstanding = 0
        
        for t in tenants:
            bal = calculate_outstanding_balance(t)
            if bal > 0:
                tenant_balances.append({
                    'tenant': t,
                    'balance': bal
                })
                total_outstanding += bal
                
        tenant_balances.sort(key=lambda x: x['balance'], reverse=True)

        return render(request, 'reports/balances.html', {
            'tenant_balances': tenant_balances,
            'total_outstanding': total_outstanding,
        })
