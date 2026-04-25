from django.urls import path
from django.contrib.auth.decorators import login_required
from dashboard import views

app_name = 'dashboard'

urlpatterns = [
    path('',                  login_required(views.AdminManagerDashboardView.as_view()), name='index'),
    path('dashboard/',        login_required(views.AdminManagerDashboardView.as_view()), name='admin'),
    path('owner/dashboard/',  login_required(views.OwnerDashboardView.as_view()),        name='owner'),
    path('staff/dashboard/',  login_required(views.StaffDashboardView.as_view()),        name='staff'),
    path('tenant/dashboard/', login_required(views.TenantDashboardView.as_view()),       name='tenant'),
    path('dashboard/chart/revenue/', login_required(views.RevenueChartDataView.as_view()), name='chart_revenue'),
    path('dashboard/partials/expiry/', login_required(views.ExpiryPanelView.as_view()),    name='expiry_panel'),
    path('reports/monthly-payments/', login_required(views.MonthlyPaymentsReportView.as_view()), name='report_monthly_payments'),
    path('reports/balances/', login_required(views.OutstandingBalancesReportView.as_view()), name='report_balances'),
]
