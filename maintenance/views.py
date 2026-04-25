from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, render, redirect
from django.utils import timezone
from .models import MaintenanceTicket, TicketTimeline
from .forms import MaintenanceTicketForm, TicketStatusUpdateForm

class TicketListView(LoginRequiredMixin, ListView):
    model = MaintenanceTicket
    template_name = 'maintenance/ticket_list.html'
    context_object_name = 'tickets'
    
    def get_queryset(self):
        qs = super().get_queryset().select_related('unit', 'reported_by', 'assigned_to')
        status = self.request.GET.get('status')
        if status:
            qs = qs.filter(status=status)
        return qs.order_by('-created_at')

class TicketDetailView(LoginRequiredMixin, DetailView):
    model = MaintenanceTicket
    template_name = 'maintenance/ticket_detail.html'
    context_object_name = 'ticket'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['timeline'] = self.object.timeline.all().select_related('actor')
        context['status_form'] = TicketStatusUpdateForm(instance=self.object)
        return context

class TicketCreateView(LoginRequiredMixin, CreateView):
    model = MaintenanceTicket
    form_class = MaintenanceTicketForm
    template_name = 'maintenance/ticket_form.html'
    success_url = reverse_lazy('maintenance:ticket_list')

    def form_valid(self, form):
        form.instance.reported_by = self.request.user
        response = super().form_valid(form)
        # Create initial timeline entry
        TicketTimeline.objects.create(
            ticket=self.object,
            actor=self.request.user,
            status=self.object.status,
            notes="Ticket created."
        )
        return response

def htmx_update_status(request, pk):
    ticket = get_object_or_404(MaintenanceTicket, pk=pk)
    if request.method == 'POST':
        form = TicketStatusUpdateForm(request.POST, request.FILES, instance=ticket)
        if form.is_valid():
            old_status = ticket.status
            ticket = form.save(commit=False)
            
            if ticket.status == 'RESOLVED' and old_status != 'RESOLVED':
                ticket.resolved_at = timezone.now()
            
            ticket.save()
            
            notes = form.cleaned_data.get('notes', '')
            TicketTimeline.objects.create(
                ticket=ticket,
                actor=request.user,
                status=ticket.status,
                notes=notes,
                cost_logged=ticket.cost if ticket.status in ['RESOLVED', 'CLOSED'] else None
            )
            
            response = render(request, 'maintenance/partials/status_badge.html', {'ticket': ticket})
            response['HX-Refresh'] = 'true'
            return response
    else:
        form = TicketStatusUpdateForm(instance=ticket)
    
    return render(request, 'maintenance/partials/status_update_form.html', {'form': form, 'ticket': ticket})
