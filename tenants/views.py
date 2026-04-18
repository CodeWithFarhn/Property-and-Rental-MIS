"""
tenants/views.py — thin controllers
"""
from django.shortcuts import render, get_object_or_404, redirect
from django.views import View
from django.http import HttpResponse
from django.db.models import Q
from django.contrib import messages

from accounts.decorators import role_required
from tenants.models import Tenant
from tenants import services
from tenants.forms import TenantAdmissionForm, TenantEditForm
from leases.services import get_active_lease
from tenants.services import calculate_outstanding_balance


class TenantListView(View):
    @role_required('ADMIN', 'MANAGER')
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def get(self, request):
        status = request.GET.get('status', 'ACTIVE')
        q      = request.GET.get('q', '').strip()
        tenants = Tenant.objects.filter(status=status).select_related('leases__unit__property')
        if q:
            tenants = tenants.filter(
                Q(full_name__icontains=q) | Q(cnic__icontains=q) | Q(phone__icontains=q)
            )
        # Annotate outstanding balance
        for t in tenants:
            t.outstanding = calculate_outstanding_balance(t)
        if request.headers.get('HX-Request'):
            return render(request, 'tenants/partials/tenant_table.html', {'tenants': tenants, 'status': status})
        return render(request, 'tenants/tenant_list.html', {'tenants': tenants, 'status': status})


class TenantListPartialView(View):
    def get(self, request):
        return TenantListView().get(request)


class TenantCreateView(View):
    @role_required('ADMIN', 'MANAGER')
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

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
        return render(request, 'tenants/tenant_add.html', {'form': form}, status=422)


class TenantDetailView(View):
    @role_required('ADMIN', 'MANAGER')
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, pk):
        tenant = get_object_or_404(Tenant, pk=pk)
        active_lease = get_active_lease(tenant.id)
        outstanding = calculate_outstanding_balance(tenant)
        invoices = tenant.leases.prefetch_related('invoices__payments').first()
        all_invoices = []
        all_payments = []
        for lease in tenant.leases.all():
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
        })


class TenantEditModalView(View):
    @role_required('ADMIN', 'MANAGER')
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

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


class TenantDeactivateView(View):
    @role_required('ADMIN', 'MANAGER')
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def post(self, request, pk):
        services.terminate_tenant(tenant_id=pk)
        messages.success(request, 'Tenant has been deactivated and unit is now vacant.')
        return redirect('tenants:list')


class CnicCheckView(View):
    """HTMX endpoint: returns inline error or green checkmark for CNIC field."""
    def get(self, request):
        cnic = request.GET.get('cnic', '').strip()
        try:
            cleaned = services.clean_cnic(cnic)
            exists = services.check_cnic_exists(cleaned)
        except ValueError:
            exists = False
            cleaned = None
        return render(request, 'tenants/partials/cnic_check.html', {
            'exists': exists, 'cnic': cleaned,
        })
