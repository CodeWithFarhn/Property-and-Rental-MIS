from django.urls import path
from accounts import views

app_name = 'accounts'

urlpatterns = [
    path('login/',  views.LoginView.as_view(),  name='login'),
    path('logout/', views.LogoutView.as_view(), name='logout'),
    path('users/', views.UserListView.as_view(), name='user_list'),
    path('users/<int:pk>/toggle-active/', views.htmx_toggle_active, name='htmx_toggle_active'),
    path('settings/', views.SettingsView.as_view(), name='settings'),
]
