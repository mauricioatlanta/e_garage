from django.shortcuts import render
from taller.models.vehiculos import Vehiculo

def dashboard_view(request):
    vehiculos = Vehiculo.objects.select_related('marca', 'modelo', 'cliente').order_by('-id')[:5]
    return render(request, 'taller/dashboard.html', {'vehiculos': vehiculos})
