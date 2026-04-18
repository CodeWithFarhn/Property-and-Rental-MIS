"""
accounts/decorators.py
@role_required decorator for view-level RBAC enforcement.

Usage on function-based views:
    @login_required
    @role_required('ADMIN', 'MANAGER')
    def my_view(request): ...

Usage on class-based views (use method_decorator on the class):
    @method_decorator(role_required('ADMIN'), name='dispatch')
    class MyView(View): ...
"""
from functools import wraps
from django.http import HttpResponseForbidden
from django.utils.decorators import method_decorator


def role_required(*roles):
    """
    Checks request.user.role against the allowed roles list.
    Returns HTTP 403 if the user's role is not permitted.
    Must be applied AFTER @login_required.
    Works correctly on both function-based and class-based views.
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped(request, *args, **kwargs):
            if not hasattr(request.user, 'role') or request.user.role not in roles:
                return HttpResponseForbidden(
                    '<h1>403 — Access Denied</h1>'
                    f'<p>Your role (<strong>{getattr(request.user, "role", "unknown")}</strong>) '
                    f'does not have access to this page.</p>'
                )
            return view_func(request, *args, **kwargs)
        return _wrapped
    return decorator
