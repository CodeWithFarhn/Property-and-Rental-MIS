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
from django.template.loader import render_to_string
try:
    import weasyprint
except (ImportError, OSError):
    weasyprint = None

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
        from properties.models import Property

        # Default ordering is newest month first, then newest created
        invoices = Invoice.objects.select_related('lease__tenant', 'lease__unit__property').order_by('-period_month', '-created_at')

        # Filters
        status = request.GET.get('status', '')
        period_month = request.GET.get('period_month', '')
        property_id = request.GET.get('property', '')
        q = request.GET.get('q', '').strip()

        if status:
            invoices = invoices.filter(status=status)
        if period_month:
            invoices = invoices.filter(period_month=period_month + "-01")
        if property_id:
            invoices = invoices.filter(lease__unit__property_id=property_id)
        if q:
            invoices = invoices.filter(
                Q(invoice_number__icontains=q) |
                Q(lease__tenant__full_name__icontains=q) |
                Q(lease__tenant__cnic__icontains=q)
            )

        today = timezone.localdate()
        context = {
            'invoices': invoices, 
            'today': today,
            'properties': Property.objects.filter(status='ACTIVE'),
            'current_filters': request.GET
        }

        if request.headers.get('HX-Request') and not request.headers.get('HX-Target') == 'modal-body':
            return render(request, 'finance/partials/invoice_list_table.html', context)
        return render(request, 'finance/invoice_list.html', context)


@method_decorator(login_required, name='dispatch')
@method_decorator(role_required('ADMIN', 'MANAGER'), name='dispatch')
class BulkInvoiceGenerateView(View):
    def post(self, request):
        today = timezone.localdate()
        # Always generate for the 1st of the current month
        current_month = today.replace(day=1)
        
        count = services.bulk_generate_invoices(current_month)
        
        response = HttpResponse(status=204)
        response['HX-Trigger'] = f'{{"showToast": {{"message": "Successfully generated {count} invoices for {current_month.strftime("%B %Y")}.", "type": "success"}}, "refreshInvoiceList": true}}'
        return response


@method_decorator(login_required, name='dispatch')
@method_decorator(role_required('ADMIN', 'MANAGER'), name='dispatch')
class InvoiceCreateModalView(View):
    def get(self, request):
        initial = {}
        if 'lease' in request.GET:
            initial['lease'] = request.GET.get('lease')
        form = InvoiceForm(user=request.user, initial=initial)
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
                response['HX-Trigger'] = f'{{"showToast": {{"message": "Invoice {invoice.invoice_number} created.", "type": "success"}}, "refreshInvoiceList": true, "closeModal": true}}'
                return response
            except ValueError as e:
                form.add_error(None, str(e))
        return render(request, 'finance/partials/invoice_form_modal.html', {'form': form})


@method_decorator(login_required, name='dispatch')
@method_decorator(role_required('ADMIN', 'MANAGER', 'STAFF'), name='dispatch')
class PaymentCreateView(View):
    def get(self, request):
        initial = {}
        tenant_id = request.GET.get('tenant')
        tenant = None
        if tenant_id:
            tenant = get_object_or_404(Tenant, pk=tenant_id)
            first_invoice = Invoice.objects.filter(lease__tenant=tenant, status__in=['UNPAID', 'PARTIAL']).order_by('due_date').first()
            if first_invoice:
                initial['invoice'] = first_invoice.id
                initial['amount_paid'] = first_invoice.remaining_balance

        form = PaymentForm(tenant_id=tenant_id, initial=initial)
        return render(request, 'finance/payment_new.html', {'form': form, 'prefill_tenant': tenant})

    def post(self, request):
        tenant_id = request.POST.get('tenant_id')
        form = PaymentForm(request.POST, tenant_id=tenant_id)
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
        
        # If form is invalid, we still want to show the prefill tenant summary
        tenant = get_object_or_404(Tenant, pk=tenant_id) if tenant_id else None
        return render(request, 'finance/payment_new.html', {'form': form, 'prefill_tenant': tenant})


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

@method_decorator(login_required, name='dispatch')
class PaymentReceiptPDFView(View):
    def get(self, request, pk):
        payment = get_object_or_404(Payment, pk=pk)
        
        # Only allow admin/manager or the tenant themselves to view
        if request.user.role not in ['ADMIN', 'MANAGER']:
            if payment.invoice.lease.tenant.user != request.user:
                return HttpResponse('Unauthorized', status=401)

        html_string = render_to_string('finance/receipt_pdf.html', {'payment': payment})
        
        if weasyprint:
            pdf_file = weasyprint.HTML(string=html_string).write_pdf()
            response = HttpResponse(pdf_file, content_type='application/pdf')
            response['Content-Disposition'] = f'inline; filename="receipt_{payment.id}.pdf"'
            return response
        else:
            # Fallback to returning raw HTML if GTK+3 is not installed on Windows
            return HttpResponse(html_string)
