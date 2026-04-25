from django.views.generic import ListView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import get_object_or_404, render
from django.http import HttpResponse
from .models import AuditLog

class AdminRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.role == 'ADMIN'

class AuditLogListView(LoginRequiredMixin, AdminRequiredMixin, ListView):
    model = AuditLog
    template_name = 'audit/audit_log.html'
    context_object_name = 'logs'
    paginate_by = 50

    def get_queryset(self):
        return super().get_queryset().select_related('actor')

def htmx_mark_seen(request, pk):
    if request.user.role != 'ADMIN':
        return HttpResponse('Unauthorized', status=401)
        
    log = get_object_or_404(AuditLog, pk=pk)
    log.seen = True
    log.save(update_fields=['seen'])
    
    return render(request, 'audit/partials/seen_badge.html', {'log': log})
