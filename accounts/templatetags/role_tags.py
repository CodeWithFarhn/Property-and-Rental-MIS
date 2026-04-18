"""
accounts/templatetags/role_tags.py
Template tags for role-based sidebar navigation rendering.
"""
from django import template

register = template.Library()


@register.simple_tag(takes_context=True)
def user_role(context):
    request = context.get('request')
    if request and request.user.is_authenticated:
        return request.user.role
    return ''


@register.inclusion_tag('partials/_sidebar_menu.html', takes_context=True)
def sidebar_menu(context):
    """Renders the role-appropriate sidebar navigation."""
    request = context.get('request')
    role = ''
    if request and request.user.is_authenticated:
        role = request.user.role
    return {'role': role, 'request': request}
