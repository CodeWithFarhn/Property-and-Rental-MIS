from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from .models import OwnerContract
from finance.models import MonthlySettlement
from .forms import OwnerContractForm, SettlementRemitForm

class AdminRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.role == 'ADMIN'

class OwnerRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.role in ['ADMIN', 'OWNER']

class ContractListView(LoginRequiredMixin, OwnerRequiredMixin, ListView):
    model = OwnerContract
    template_name = 'contracts/contract_list.html'
    context_object_name = 'contracts'

    def get_queryset(self):
        qs = super().get_queryset().select_related('owner').order_by('-created_at')
        if self.request.user.role == 'OWNER':
            qs = qs.filter(owner=self.request.user)
        return qs

class ContractCreateView(LoginRequiredMixin, AdminRequiredMixin, CreateView):
    model = OwnerContract
    form_class = OwnerContractForm
    template_name = 'contracts/contract_detail.html'
    success_url = reverse_lazy('contracts:contract_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['is_create'] = True
        return context

class OwnerContractDetailView(LoginRequiredMixin, OwnerRequiredMixin, DetailView):
    model = OwnerContract
    template_name = 'contracts/owner_contract_detail.html'
    context_object_name = 'contract'

    def get_queryset(self):
        qs = super().get_queryset().select_related('owner')
        if self.request.user.role == 'OWNER':
            qs = qs.filter(owner=self.request.user)
        return qs

class SettlementListView(LoginRequiredMixin, AdminRequiredMixin, ListView):
    model = MonthlySettlement
    template_name = 'finance/settlements_list.html'
    context_object_name = 'settlements'

    def get_queryset(self):
        return super().get_queryset().select_related('contract__owner', 'property').order_by('-period_month')

class OwnerSettlementListView(LoginRequiredMixin, OwnerRequiredMixin, ListView):
    model = MonthlySettlement
    template_name = 'finance/owner_settlements.html'
    context_object_name = 'settlements'

    def get_queryset(self):
        return super().get_queryset().select_related('contract', 'property').filter(contract__owner=self.request.user).order_by('-period_month')

def remit_settlement(request, pk):
    if request.user.role != 'ADMIN':
        return redirect('dashboard:index')
        
    settlement = get_object_or_404(MonthlySettlement, pk=pk)
    if request.method == 'POST':
        form = SettlementRemitForm(request.POST, request.FILES, instance=settlement)
        if form.is_valid():
            settlement = form.save(commit=False)
            settlement.status = 'REMITTED'
            settlement.remitted_at = timezone.now()
            settlement.save()
            return redirect('contracts:settlement_list')
    return redirect('contracts:settlement_list')
