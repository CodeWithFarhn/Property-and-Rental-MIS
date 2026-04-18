"""finance/views.py"""
from decimal import Decimal
from django.shortcuts import render, get_object_or_404, redirect
from django.views import View
from django.http import HttpResponse
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.contrib import messages
from django.utils import timezone

from accounts.decorators import role_required
from finance.models import Invoice, Payment
from finance import services
from finance.forms import InvoiceForm, PaymentForm
from tenants.models import Tenant
from tenants.services import calculate_outstanding_balance
from leases.models import Lease


@method_decorator(login_required, name='dispatch')
@method_decorator(role_required('ADMIN', 'MANAGER'), name='dispatch')
class InvoiceListView(View):
    def get(self, request):
        status = request.GET.get('status', '')
        invoices = Invoice.objects.select_related('lease__tenant', 'lease__unit__property').order_by('-created_at')
        if status:
            invoices = invoices.filter(status=status)
        today = timezone.localdate()
        if request.headers.get('HX-Request'):
            return render(request, 'finance/partials/invoice_list_table.html', {'invoices': invoices, 'today': today})
        return render(request, 'finance/invoice_list.html', {'invoices': invoices, 'today': today})


@method_decorator(login_required, name='dispatch')
@method_decorator(role_required('ADMIN', 'MANAGER'), name='dispatch')
class InvoiceCreateModalView(View):
    def get(self, request):
        form = InvoiceForm(user=request.user)
        return render(request, 'finance/partials/invoice_form_modal.html', {'form': form})

    def post(self, request):
        form = InvoiceForm(request.POST, user=request.user)
        if form.is_valid():
            try:
                invoice = services.create_invoice(
                    lease=form.cleaned_data['lease'],
                    period_month=form.cleaned_data['period_month'],
                    notes=form.cleaned_data.get('notes', ''),
                )
                response = HttpResponse(status=204)
                response['HX-Trigger'] = f'{{"showToast": {{"message": "Invoice {invoice.invoice_number} created.", "type": "success"}}, "refreshInvoiceList": true}}'
                return response
            except ValueError as e:
                form.add_error(None, str(e))
        return render(request, 'finance/partials/invoice_form_modal.html', {'form': form}, status=422)


@method_decorator(login_required, name='dispatch')
@method_decorator(role_required('ADMIN', 'MANAGER', 'STAFF'), name='dispatch')
class PaymentCreateView(View):
    def get(self, request):
        form = PaymentForm()
        return render(request, 'finance/payment_new.html', {'form': form})

    def post(self, request):
        form = PaymentForm(request.POST)
        if form.is_valid():
            try:
                payment = services.record_payment(
                    invoice_id=form.cleaned_data['invoice'].id,
                    amount_paid=form.cleaned_data['amount_paid'],
                    payment_method=form.cleaned_data['payment_method'],
                    date_paid=form.cleaned_data['date_paid'],
                    recorded_by_id=request.user.id,
                    reference_code=form.cleaned_data.get('reference_code', ''),
                    notes=form.cleaned_data.get('notes', ''),
                )
                messages.success(request, f'Payment of PKR {payment.amount_paid:,.0f} recorded successfully.')
                return redirect('finance:payment_list')
            except Exception as e:
                form.add_error(None, str(e))
        return render(request, 'finance/payment_new.html', {'form': form})


@method_decorator(login_required, name='dispatch')
@method_decorator(role_required('ADMIN', 'MANAGER'), name='dispatch')
class PaymentListView(View):
    def get(self, request):
        payments = Payment.objects.select_related('invoice__lease__tenant', 'recorded_by').order_by('-date_paid')
        if request.headers.get('HX-Request'):
            return render(request, 'finance/partials/payment_list_table.html', {'payments': payments})
        return render(request, 'finance/payment_list.html', {'payments': payments})


@method_decorator(login_required, name='dispatch')
class TenantSearchView(View):
    def get(self, request):
        q = request.GET.get('q', '').strip()
        tenants = []
        if len(q) >= 3:
            tenants = Tenant.objects.filter(
                Q(full_name__icontains=q) | Q(cnic__icontains=q),
                status='ACTIVE'
            )[:10]
        return render(request, 'finance/partials/tenant_search_results.html', {'tenants': tenants, 'q': q})


@method_decorator(login_required, name='dispatch')
class TenantSummaryView(View):
    def get(self, request):
        tenant_id = request.GET.get('tenant')
        if not tenant_id:
            return HttpResponse('<p class="p-3 text-muted text-center">Select a tenant to see their balance.</p>')
        tenant = get_object_or_404(Tenant, pk=tenant_id)
        outstanding = calculate_outstanding_balance(tenant)
        unpaid_invoices = Invoice.objects.filter(
            lease__tenant=tenant, status__in=['UNPAID', 'PARTIAL']
        ).order_by('due_date')
        return render(request, 'finance/partials/tenant_payment_summary.html', {
            'tenant': tenant,
            'outstanding': outstanding,
            'unpaid_invoices': unpaid_invoices,
        })
