"""
accounts/decorators.py
@role_required decorator for view-level RBAC enforcement.
Usage:
    @login_required
    @role_required('ADMIN', 'MANAGER')
    def my_view(request): ...
"""
from functools import wraps
from django.http import HttpResponseForbidden
from django.contrib.auth.decorators import login_required


def role_required(*roles):
    """
    Decorator that checks request.user.role against the allowed roles list.
    Returns HTTP 403 if the user's role is not permitted.
    Must be applied AFTER @login_required.
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped(request, *args, **kwargs):
            if not hasattr(request.user, 'role') or request.user.role not in roles:
                return HttpResponseForbidden(
                    '<h1>403 Forbidden</h1>'
                    '<p>You do not have permission to access this page.</p>'
                )
            return view_func(request, *args, **kwargs)
        return _wrapped
    return decorator
