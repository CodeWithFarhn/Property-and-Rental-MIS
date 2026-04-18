"""
accounts/views.py  — thin controllers, all logic in services.py
"""
from django.shortcuts import render, redirect
from django.views import View
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator

from accounts.forms import LoginForm
from accounts.services import authenticate_user, logout_user, get_role_redirect_url


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
