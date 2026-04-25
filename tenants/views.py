"""tenants/views.py"""
from django.shortcuts import render, get_object_or_404, redirect
from django.views import View
from django.http import HttpResponse
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.contrib import messages
from decimal import Decimal

from accounts.decorators import role_required
from tenants.models import Tenant
from tenants import services
from tenants.forms import TenantAdmissionForm, TenantEditForm
from leases.services import get_active_lease
from tenants.services import calculate_outstanding_balance


@method_decorator(login_required, name='dispatch')
@method_decorator(role_required('ADMIN', 'MANAGER'), name='dispatch')
class TenantListView(View):
    def get(self, request):
        status = request.GET.get('status', 'ACTIVE')
        q      = request.GET.get('q', '').strip()
        from django.db.models.functions import Coalesce
        from django.db.models import Sum, OuterRef, Subquery
        from finance.models import Invoice, Payment

        total_invoiced = Invoice.objects.filter(
            lease__tenant=OuterRef('pk')
        ).values('lease__tenant').annotate(
            t=Sum('amount_due')
        ).values('t')

        total_paid = Payment.objects.filter(
            invoice__lease__tenant=OuterRef('pk')
        ).values('invoice__lease__tenant').annotate(
            t=Sum('amount_paid')
        ).values('t')

        tenants = Tenant.objects.filter(status=status).prefetch_related('leases__unit__property').annotate(
            outstanding=Coalesce(Subquery(total_invoiced), Decimal('0.00')) - Coalesce(Subquery(total_paid), Decimal('0.00'))
        )

        if q:
            tenants = tenants.filter(
                Q(full_name__icontains=q) | Q(cnic__icontains=q) | Q(phone__icontains=q)
            )
        if request.headers.get('HX-Request'):
            return render(request, 'tenants/partials/tenant_table.html', {'tenants': tenants, 'status': status})
        return render(request, 'tenants/tenant_list.html', {'tenants': tenants, 'status': status})


@method_decorator(login_required, name='dispatch')
@method_decorator(role_required('ADMIN', 'MANAGER'), name='dispatch')
class TenantListPartialView(View):
    def get(self, request):
        return TenantListView.as_view()(request)


@method_decorator(login_required, name='dispatch')
@method_decorator(role_required('ADMIN', 'MANAGER'), name='dispatch')
class TenantCreateView(View):
    def get(self, request):
        form = TenantAdmissionForm()
        return render(request, 'tenants/tenant_add.html', {'form': form})

    def post(self, request):
        form = TenantAdmissionForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                tenant = services.admit_tenant(
                    tenant_data=form.get_tenant_data(),
                    lease_data=form.get_lease_data(),
                    unit_id=form.cleaned_data['unit'].id,
                )
                messages.success(request, f"Tenant '{tenant.full_name}' admitted successfully.")
                return redirect('tenants:detail', pk=tenant.pk)
            except Exception as e:
                form.add_error(None, str(e))
        return render(request, 'tenants/tenant_add.html', {'form': form})


@method_decorator(login_required, name='dispatch')
@method_decorator(role_required('ADMIN', 'MANAGER'), name='dispatch')
class TenantDetailView(View):
    def get(self, request, pk):
        from django.utils import timezone
        tenant = get_object_or_404(Tenant, pk=pk)
        active_lease = get_active_lease(tenant.id)
        outstanding = calculate_outstanding_balance(tenant)
        all_invoices = []
        all_payments = []
        for lease in tenant.leases.prefetch_related('invoices__payments').all():
            for inv in lease.invoices.all():
                all_invoices.append(inv)
                for pay in inv.payments.all():
                    all_payments.append(pay)
        return render(request, 'tenants/tenant_detail.html', {
            'tenant': tenant,
            'active_lease': active_lease,
            'outstanding': outstanding,
            'invoices': all_invoices,
            'payments': all_payments,
            'today': timezone.localdate(),
        })


@method_decorator(login_required, name='dispatch')
@method_decorator(role_required('ADMIN', 'MANAGER'), name='dispatch')
class TenantEditModalView(View):
    def get(self, request, pk):
        tenant = get_object_or_404(Tenant, pk=pk)
        form = TenantEditForm(instance=tenant)
        return render(request, 'tenants/partials/tenant_edit_modal.html', {'form': form, 'tenant': tenant})

    def post(self, request, pk):
        tenant = get_object_or_404(Tenant, pk=pk)
        form = TenantEditForm(request.POST, request.FILES, instance=tenant)
        if form.is_valid():
            form.save()
            response = HttpResponse(status=204)
            response['HX-Trigger'] = '{"showToast": {"message": "Tenant details updated.", "type": "success"}}'
            return response
        return render(request, 'tenants/partials/tenant_edit_modal.html', {'form': form, 'tenant': tenant}, status=422)


@method_decorator(login_required, name='dispatch')
@method_decorator(role_required('ADMIN', 'MANAGER'), name='dispatch')
class TenantDeactivateView(View):
    def post(self, request, pk):
        services.terminate_tenant(tenant_id=pk)
        messages.success(request, 'Tenant deactivated. Unit is now vacant.')
        return redirect('tenants:list')


@method_decorator(login_required, name='dispatch')
class CnicCheckView(View):
    def get(self, request):
        cnic = request.GET.get('cnic', '').strip()
        error = None
        cleaned = None
        exists = False
        if cnic:
            try:
                cleaned = services.clean_cnic(cnic)
                exists = services.check_cnic_exists(cleaned)
            except ValueError as e:
                error = str(e)
        return render(request, 'tenants/partials/cnic_check.html', {
            'exists': exists, 'cnic': cleaned, 'error': error, 'raw_cnic': cnic
        })
