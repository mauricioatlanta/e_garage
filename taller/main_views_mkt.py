from django.shortcuts import render

def landing_mecanicos(request):
    return render(request, 'landing_mecanicos.html')

def landing_repuestos(request):
    return render(request, 'landing_repuestos.html')

def landing_servicios(request):
    return render(request, 'landing_servicios.html')

def landing_reportes(request):
    return render(request, 'landing_reportes.html')

def landing_clientes(request):
    return render(request, 'landing_clientes.html')

def landing_ia(request):
    return render(request, 'landing_ia.html')
