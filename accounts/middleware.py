"""
accounts/middleware.py

SessionTimeoutMiddleware:
  - Logs out users who have been inactive for > SESSION_COOKIE_AGE seconds.
  - Redirects to /accounts/login/?timeout=1 so the template can show a banner.
"""
from django.conf import settings
from django.http import HttpResponseRedirect
from django.utils import timezone
from django.urls import reverse


class SessionTimeoutMiddleware:
    """Auto-logout after SESSION_COOKIE_AGE seconds of inactivity."""

    EXEMPT_PATHS = ('/accounts/login/', '/accounts/logout/')

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if (
            request.user.is_authenticated
            and request.path not in self.EXEMPT_PATHS
        ):
            last_activity_str = request.session.get('last_activity')
            if last_activity_str:
                last_activity = timezone.datetime.fromisoformat(last_activity_str)
                # Make it timezone-aware if USE_TZ is True
                if timezone.is_naive(last_activity):
                    last_activity = timezone.make_aware(last_activity)
                elapsed = (timezone.now() - last_activity).total_seconds()
                timeout = getattr(settings, 'SESSION_COOKIE_AGE', 1800)
                if elapsed > timeout:
                    from django.contrib.auth import logout
                    logout(request)
                    login_url = reverse('accounts:login')
                    next_url = request.get_full_path()
                    return HttpResponseRedirect(
                        f'{login_url}?timeout=1&next={next_url}'
                    )
            # Update last activity on every request
            request.session['last_activity'] = timezone.now().isoformat()

        return self.get_response(request)
