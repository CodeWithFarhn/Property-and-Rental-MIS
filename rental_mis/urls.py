"""
rental_mis/urls.py — Master URL configuration
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import redirect

urlpatterns = [
    path('admin/',     admin.site.urls),
    path('accounts/',  include('accounts.urls',    namespace='accounts')),
    path('',           include('dashboard.urls',   namespace='dashboard')),
    path('properties/',include('properties.urls',  namespace='properties')),
    path('tenants/',   include('tenants.urls',     namespace='tenants')),
    path('finance/',   include('finance.urls',     namespace='finance')),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
