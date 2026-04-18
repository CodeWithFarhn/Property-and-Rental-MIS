from django.urls import path
from django.contrib.auth.decorators import login_required
from tenants import views

app_name = 'tenants'

urlpatterns = [
    path('',                        login_required(views.TenantListView.as_view()),      name='list'),
    path('add/',                    login_required(views.TenantCreateView.as_view()),    name='add'),
    path('<int:pk>/',               login_required(views.TenantDetailView.as_view()),    name='detail'),
    path('<int:pk>/edit/',          login_required(views.TenantEditModalView.as_view()), name='edit'),
    path('<int:pk>/deactivate/',    login_required(views.TenantDeactivateView.as_view()),name='deactivate'),
    # HTMX endpoints
    path('check-cnic/',             login_required(views.CnicCheckView.as_view()),       name='check_cnic'),
    path('partial/',                login_required(views.TenantListPartialView.as_view()),name='list_partial'),
]
