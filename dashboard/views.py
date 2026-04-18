"""dashboard/views.py — thin controllers, all logic in dashboard/services.py"""
import json
from django.shortcuts import render, redirect
from django.views import View
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required

from accounts.decorators import role_required
from accounts.services import get_role_redirect_url
from dashboard import services
from leases.services import get_expiring_leases


class AdminManagerDashboardView(View):
    @role_required('ADMIN', 'MANAGER')
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def get(self, request):
        kpis = services.get_admin_kpis()
        expiring = get_expiring_leases(days=30)
        audit_entries = services.get_recent_audit_entries()
        return render(request, 'dashboard/admin_dashboard.html', {
            'kpis': kpis,
            'expiring_leases': expiring,
            'audit_entries': audit_entries,
        })


class OwnerDashboardView(View):
    @role_required('OWNER')
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def get(self, request):
        kpis = services.get_admin_kpis(owner_id=request.user.id)
        expiring = get_expiring_leases(days=30)
        return render(request, 'dashboard/owner_dashboard.html', {
            'kpis': kpis,
            'expiring_leases': expiring,
        })


class StaffDashboardView(View):
    @role_required('STAFF')
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

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


class TenantDashboardView(View):
    @role_required('TENANT')
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def get(self, request):
        try:
            tenant = request.user.tenant_profile
        except Exception:
            tenant = None
        return render(request, 'dashboard/tenant_dashboard.html', {'tenant': tenant})


class RevenueChartDataView(View):
    @role_required('ADMIN', 'MANAGER', 'OWNER')
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def get(self, request):
        owner_id = request.user.id if request.user.role == 'OWNER' else None
        data = services.get_revenue_chart_data(months=6, owner_id=owner_id)
        return JsonResponse(data, safe=False)


class ExpiryPanelView(View):
    def get(self, request):
        expiring = get_expiring_leases(days=30)
        return render(request, 'dashboard/partials/expiry_panel.html', {
            'expiring_leases': expiring,
        })
