from django.urls import path
from django.contrib.auth.decorators import login_required
from finance import views

app_name = 'finance'

urlpatterns = [
    # Invoices
    path('invoices/',              login_required(views.InvoiceListView.as_view()),        name='invoice_list'),
    path('invoices/add/',          login_required(views.InvoiceCreateModalView.as_view()), name='invoice_add'),
    # Payments
    path('payments/',              login_required(views.PaymentListView.as_view()),        name='payment_list'),
    path('payments/new/',          login_required(views.PaymentCreateView.as_view()),      name='payment_new'),
    # HTMX endpoints
    path('payments/tenant-search/', login_required(views.TenantSearchView.as_view()),     name='tenant_search'),
    path('payments/tenant-summary/',login_required(views.TenantSummaryView.as_view()),    name='tenant_summary'),
]
