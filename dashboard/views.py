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


@method_decorator(login_required, name='dispatch')
@method_decorator(role_required('ADMIN', 'MANAGER'), name='dispatch')
class AdminManagerDashboardView(View):
    def get(self, request):
        kpis = services.get_admin_kpis()
        expiring = get_expiring_leases(days=30)
        audit_entries = services.get_recent_audit_entries()
        return render(request, 'dashboard/admin_dashboard.html', {
            'kpis': kpis,
            'expiring_leases': expiring,
            'audit_entries': audit_entries,
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
