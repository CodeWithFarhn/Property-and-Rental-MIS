from django.urls import path
from . import views

app_name = 'audit'

urlpatterns = [
    path('', views.AuditLogListView.as_view(), name='log_list'),
    path('<int:pk>/seen/', views.htmx_mark_seen, name='htmx_mark_seen'),
]
