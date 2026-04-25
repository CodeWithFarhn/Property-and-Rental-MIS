"""
accounts/views.py  — thin controllers, all logic in services.py
"""
from django.shortcuts import render, redirect
from django.views import View
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator

from accounts.forms import LoginForm
from accounts.services import authenticate_user, logout_user, get_role_redirect_url
from django.views.generic import ListView
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.http import HttpResponse

User = get_user_model()

class AdminRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.role == 'ADMIN'


class LoginView(View):
    template_name = 'accounts/login.html'

    def get(self, request):
        if request.user.is_authenticated:
            return redirect(get_role_redirect_url(request.user))
        timeout = request.GET.get('timeout') == '1'
        return render(request, self.template_name, {
            'form': LoginForm(),
            'show_timeout_banner': timeout,
            'next': request.GET.get('next', ''),
        })

    def post(self, request):
        form = LoginForm(request.POST)
        if form.is_valid():
            user, error = authenticate_user(
                request,
                username=form.cleaned_data['username'],
                password=form.cleaned_data['password'],
            )
            if user:
                next_url = request.POST.get('next') or get_role_redirect_url(user)
                return redirect(next_url)
            return render(request, self.template_name, {
                'form': form,
                'error': error,
            })
        return render(request, self.template_name, {'form': form})


@method_decorator(login_required, name='dispatch')
class LogoutView(View):
    def post(self, request):
        logout_user(request)
        return redirect('accounts:login')

class UserListView(LoginRequiredMixin, AdminRequiredMixin, ListView):
    model = User
    template_name = 'accounts/user_list.html'
    context_object_name = 'users'
    
    def get_queryset(self):
        return super().get_queryset().order_by('role', 'username')

def htmx_toggle_active(request, pk):
    if request.user.role != 'ADMIN':
        return HttpResponse('Unauthorized', status=401)
        
    user = get_object_or_404(User, pk=pk)
    if user != request.user:
        user.is_active = not user.is_active
        user.save(update_fields=['is_active'])
        
    return render(request, 'accounts/partials/active_toggle.html', {'user': user})

class SettingsView(LoginRequiredMixin, AdminRequiredMixin, View):
    def get(self, request):
        return render(request, 'accounts/settings.html')
        
    def post(self, request):
        # Dummy save logic for demo
        import time
        time.sleep(1) # simulate saving
        return render(request, 'accounts/partials/settings_success.html')
