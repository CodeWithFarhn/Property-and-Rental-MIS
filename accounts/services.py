"""
accounts/services.py
Business logic for authentication and user management.
Views call these functions — no HTTP logic here.
"""
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.utils import timezone


# Role → dashboard URL mapping
_ROLE_DASHBOARD_MAP = {
    'ADMIN':   '/dashboard/',
    'MANAGER': '/dashboard/',
    'STAFF':   '/staff/dashboard/',
    'OWNER':   '/owner/dashboard/',
    'TENANT':  '/tenant/dashboard/',
}


def get_role_redirect_url(user) -> str:
    """Return the correct dashboard URL for a given user role."""
    return _ROLE_DASHBOARD_MAP.get(user.role, '/dashboard/')


def authenticate_user(request, username: str, password: str):
    """
    Authenticate credentials and log the user in.
    Returns (user, error_message).
    error_message is None on success.
    """
    user = authenticate(request, username=username, password=password)
    if user is None:
        return None, 'Invalid email or password.'
    if not user.is_active:
        return None, 'This account has been deactivated. Contact your administrator.'
    auth_login(request, user)
    request.session['last_activity'] = timezone.now().isoformat()
    return user, None


def logout_user(request) -> None:
    """Log the user out and flush their session."""
    auth_logout(request)


def deactivate_user(user_id: int) -> None:
    """
    Deactivate a user account (soft disable — does not delete).
    Their session will expire naturally within SESSION_COOKIE_AGE.
    """
    from accounts.models import CustomUser
    CustomUser.objects.filter(pk=user_id).update(is_active=False)
