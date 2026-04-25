from django.urls import path
from . import views

app_name = 'contracts'

urlpatterns = [
    path('', views.ContractListView.as_view(), name='contract_list'),
    path('new/', views.ContractCreateView.as_view(), name='contract_create'),
    path('<int:pk>/', views.OwnerContractDetailView.as_view(), name='contract_detail'),
    path('settlements/', views.SettlementListView.as_view(), name='settlement_list'),
    path('settlements/owner/', views.OwnerSettlementListView.as_view(), name='owner_settlement_list'),
    path('settlements/<int:pk>/remit/', views.remit_settlement, name='remit_settlement'),
]
