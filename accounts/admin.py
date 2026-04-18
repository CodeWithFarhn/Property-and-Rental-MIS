from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from accounts.models import CustomUser

@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'full_name', 'role', 'is_active')
    list_filter  = ('role', 'is_active')
    fieldsets = UserAdmin.fieldsets + (
        ('Role & Contact', {'fields': ('full_name', 'phone', 'role')}),
    )
