from django.urls import path
from django.contrib.auth.decorators import login_required
from properties import views

app_name = 'properties'

urlpatterns = [
    path('',                              login_required(views.PropertyListView.as_view()),      name='list'),
    path('add/',                          login_required(views.PropertyCreateView.as_view()),    name='add'),
    path('<int:pk>/edit/',                login_required(views.PropertyUpdateView.as_view()),    name='edit'),
    path('<int:pk>/units/',               login_required(views.UnitListView.as_view()),          name='unit_list'),
    path('<int:pk>/units/add/',           login_required(views.UnitCreateView.as_view()),        name='unit_add'),
    path('units/<int:pk>/edit/',          login_required(views.UnitUpdateView.as_view()),        name='unit_edit'),
    # HTMX endpoints
    path('units/vacant/',                 login_required(views.VacantUnitsView.as_view()),       name='vacant_units'),
    path('units/<int:pk>/info/',          login_required(views.UnitInfoView.as_view()),          name='unit_info'),
]
