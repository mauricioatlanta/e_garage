from django.shortcuts import render
from django.http import JsonResponse
from django.db.models import Q
from taller.models.repuesto import Repuesto

def dashboard_repuestos(request):
    return render(request, 'taller/repuestos/dashboard.html')

def lista_repuestos(request):
    q = request.GET.get('q', '').strip()
    tienda = request.GET.get('tienda', '').strip()
    repuestos = Repuesto.objects.select_related('tienda').all()
    if q:
        repuestos = repuestos.filter(
            Q(nombre_repuesto__icontains=q) |
            Q(part_number__icontains=q)
        )
    if tienda:
        repuestos = repuestos.filter(tienda__id=tienda)
    repuestos = repuestos.order_by('nombre_repuesto')
    # Para el filtro de tiendas
    tiendas = Repuesto.objects.values_list('tienda__id', 'tienda__nombre').distinct().order_by('tienda__nombre')
    return render(request, 'taller/repuestos/listar_repuestos.html', {
        'repuestos': repuestos,
        'q': q,
        'tienda': tienda,
        'tiendas': tiendas,
    })

def crear_repuesto(request):
    from taller.models.tienda import Tienda
    if request.method == 'POST':
        tienda_id = request.POST.get('tienda')
        nombre_repuesto = request.POST.get('nombre_repuesto')
        part_number = request.POST.get('part_number')
        precio_compra = request.POST.get('precio_compra')
        precio_venta = request.POST.get('precio_venta')
        stock = request.POST.get('stock')
        observaciones = request.POST.get('observaciones')
        tienda = Tienda.objects.get(id=tienda_id) if tienda_id else None
        if tienda and nombre_repuesto and part_number and precio_compra and precio_venta and stock:
            from taller.models.repuesto import Repuesto
            Repuesto.objects.create(
                tienda=tienda,
                nombre_repuesto=nombre_repuesto,
                part_number=part_number,
                precio_compra=precio_compra,
                precio_venta=precio_venta,
                stock=stock,
                observaciones=observaciones
            )
            from django.shortcuts import redirect
            return redirect('repuestos:lista_repuestos')
    tiendas = Tienda.objects.all().order_by('nombre')
    return render(request, 'taller/repuestos/agregar_repuesto.html', {'tiendas': tiendas})

def editar_repuesto(request, repuesto_id):
    return render(request, 'taller/repuestos/editar_repuesto.html', {'repuesto_id': repuesto_id})

def eliminar_repuesto(request, repuesto_id):
    return render(request, 'taller/repuestos/eliminar_repuesto.html', {'repuesto_id': repuesto_id})

def validar_part_number(request):
    # Simulación de validación
    return render(request, 'taller/repuestos/validar_part_number.html')

def api_autocomplete_repuesto(request):
    q = request.GET.get('q', '').strip()
    repuestos = Repuesto.objects.all()
    if q:
        repuestos = repuestos.filter(
            Q(nombre_repuesto__icontains=q) |
            Q(part_number__icontains=q)
        )
    repuestos = repuestos.order_by('nombre_repuesto')[:10]
    data = [
        {
            'part_number': r.part_number,
            'nombre_repuesto': r.nombre_repuesto,
            'precio_venta': float(r.precio_venta),
        }
        for r in repuestos
    ]
    return JsonResponse({'results': data})
