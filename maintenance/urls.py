from django.urls import path
from . import views

app_name = 'maintenance'

urlpatterns = [
    path('', views.TicketListView.as_view(), name='ticket_list'),
    path('new/', views.TicketCreateView.as_view(), name='ticket_create'),
    path('<int:pk>/', views.TicketDetailView.as_view(), name='ticket_detail'),
    path('<int:pk>/status/update/', views.htmx_update_status, name='htmx_update_status'),
]
