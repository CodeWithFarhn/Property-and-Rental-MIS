"""properties/views.py"""
from django.shortcuts import render, get_object_or_404, redirect
from django.views import View
from django.http import JsonResponse, HttpResponse
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from django.db.models import Q

from accounts.decorators import role_required
from properties.models import Property, Unit, Location
from properties import services
from properties.forms import PropertyForm, UnitForm


@method_decorator(login_required, name='dispatch')
@method_decorator(role_required('ADMIN', 'MANAGER'), name='dispatch')
class PropertyListView(View):
    def get(self, request):
        q = request.GET.get('q', '').strip()
        properties = Property.objects.filter(status='ACTIVE').select_related('owner', 'location')
        if q:
            properties = properties.filter(Q(name__icontains=q) | Q(location__name__icontains=q))
        for prop in properties:
            prop.occupancy = services.get_property_occupancy(prop.id)
        if request.headers.get('HX-Request'):
            return render(request, 'properties/partials/property_card_grid.html', {'properties': properties})
        return render(request, 'properties/property_list.html', {'properties': properties})


@method_decorator(login_required, name='dispatch')
@method_decorator(role_required('ADMIN', 'MANAGER'), name='dispatch')
class PropertyCreateView(View):
    def get(self, request):
        form = PropertyForm(user=request.user)
        return render(request, 'properties/partials/property_form_modal.html', {'form': form})

    def post(self, request):
        form = PropertyForm(request.POST, user=request.user)
        if form.is_valid():
            form.save()
            response = HttpResponse(status=204)
            response['HX-Trigger'] = '{"showToast": {"message": "Property added successfully.", "type": "success"}, "refreshPropertyList": true, "closeModal": true}'
            return response
        return render(request, 'properties/partials/property_form_modal.html', {'form': form})


@method_decorator(login_required, name='dispatch')
@method_decorator(role_required('ADMIN', 'MANAGER'), name='dispatch')
class PropertyUpdateView(View):
    def get(self, request, pk):
        prop = get_object_or_404(Property, pk=pk)
        form = PropertyForm(instance=prop, user=request.user)
        return render(request, 'properties/partials/property_form_modal.html', {'form': form, 'property': prop})

    def post(self, request, pk):
        prop = get_object_or_404(Property, pk=pk)
        form = PropertyForm(request.POST, instance=prop, user=request.user)
        if form.is_valid():
            form.save()
            response = HttpResponse(status=204)
            response['HX-Trigger'] = '{"showToast": {"message": "Property updated.", "type": "success"}, "refreshPropertyList": true, "closeModal": true}'
            return response
        return render(request, 'properties/partials/property_form_modal.html', {'form': form, 'property': prop})


@method_decorator(login_required, name='dispatch')
@method_decorator(role_required('ADMIN', 'MANAGER'), name='dispatch')
class UnitListView(View):
    def get(self, request, pk):
        prop = get_object_or_404(Property, pk=pk)
        units = prop.units.all()
        occupancy = services.get_property_occupancy(pk)
        return render(request, 'properties/unit_list.html', {
            'property': prop, 'units': units, 'occupancy': occupancy,
        })


@method_decorator(login_required, name='dispatch')
@method_decorator(role_required('ADMIN', 'MANAGER'), name='dispatch')
class UnitCreateView(View):
    def get(self, request, pk):
        prop = get_object_or_404(Property, pk=pk)
        form = UnitForm()
        return render(request, 'properties/partials/unit_form_modal.html', {'form': form, 'property': prop})

    def post(self, request, pk):
        prop = get_object_or_404(Property, pk=pk)
        form = UnitForm(request.POST)
        if form.is_valid():
            unit = form.save(commit=False)
            unit.property = prop
            unit.save()
            response = HttpResponse(status=204)
            response['HX-Trigger'] = '{"showToast": {"message": "Unit added.", "type": "success"}, "refreshUnitList": true, "closeModal": true}'
            return response
        return render(request, 'properties/partials/unit_form_modal.html', {'form': form, 'property': prop})


@method_decorator(login_required, name='dispatch')
@method_decorator(role_required('ADMIN', 'MANAGER'), name='dispatch')
class UnitUpdateView(View):
    def get(self, request, pk):
        unit = get_object_or_404(Unit, pk=pk)
        form = UnitForm(instance=unit)
        return render(request, 'properties/partials/unit_form_modal.html', {'form': form, 'unit': unit, 'property': unit.property})

    def post(self, request, pk):
        unit = get_object_or_404(Unit, pk=pk)
        form = UnitForm(request.POST, instance=unit)
        if form.is_valid():
            form.save()
            response = HttpResponse(status=204)
            response['HX-Trigger'] = '{"showToast": {"message": "Unit updated.", "type": "success"}, "refreshUnitList": true, "closeModal": true}'
            return response
        return render(request, 'properties/partials/unit_form_modal.html', {'form': form, 'unit': unit, 'property': unit.property})


@method_decorator(login_required, name='dispatch')
class VacantUnitsView(View):
    def get(self, request):
        property_id = request.GET.get('property')
        units = services.get_vacant_units(property_id=property_id)
        return render(request, 'properties/partials/vacant_unit_options.html', {'units': units})


@method_decorator(login_required, name='dispatch')
class UnitInfoView(View):
    def get(self, request, pk=None):
        if not pk:
            pk = request.GET.get('unit')
        if not pk:
            return HttpResponse('')
            
        info = services.get_unit_info(pk)
        if not info:
            return HttpResponse('')
        return render(request, 'properties/partials/unit_info.html', info)
