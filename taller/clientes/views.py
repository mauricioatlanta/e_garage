# Búsqueda AJAX de clientes por nombre, apellido, email o teléfono
from taller.models.clientes import Cliente
from django.db import models
def ajax_buscar_clientes(request):
    q = request.GET.get("q", "").strip()
    if not q:
        return JsonResponse([], safe=False)
    clientes = Cliente.objects.filter(
        models.Q(nombre__icontains=q) |
        models.Q(apellido__icontains=q) |
        models.Q(email__icontains=q) |
        models.Q(telefono__icontains=q)
    )[:20]
    data = [
        {
            "id": c.pk,
            "nombre": c.nombre,
            "apellido": c.apellido,
            "email": c.email,
            "telefono": c.telefono,
        }
        for c in clientes
    ]
    return JsonResponse(data, safe=False)
import logging
from django.http import JsonResponse
from taller.models.region_ciudad import TallerCiudad
from taller.models.ubicacion import Ciudad

# Devuelve las ciudades de una región (por id de región)
def obtener_ciudades(request):
    region_id = request.GET.get('region_id')
    if not region_id:
        return JsonResponse([], safe=False)
    ciudades = TallerCiudad.objects.filter(region_id=region_id).values('id', 'nombre')
    return JsonResponse(list(ciudades), safe=False)

# Devuelve las ciudades de un estado de EE.UU. (por id de estado)
def obtener_ciudades_usa(request):
    estado_id = request.GET.get('estado_id')
    if not estado_id:
        return JsonResponse([], safe=False)
    ciudades = Ciudad.objects.filter(estado_id=estado_id).values('id', 'nombre')
    return JsonResponse(list(ciudades), safe=False)
import logging
from .views_cbv import (
    ClienteListView, ClienteDetailView, ClienteCreateView, ClienteUpdateView,
)

log = logging.getLogger(__name__)

def lista_clientes(request, *args, **kwargs):
    log.info("FBV shim: lista_clientes")
    return ClienteListView.as_view()(request, *args, **kwargs)

def ver_cliente(request, *args, **kwargs):
    log.info("FBV shim: ver_cliente")
    return ClienteDetailView.as_view()(request, *args, **kwargs)

def crear_cliente(request, *args, **kwargs):
    log.info("FBV shim: crear_cliente")
    # Pasar empresa explícitamente al formulario
    empresa = getattr(request.user, 'empresa', None)
    view = ClienteCreateView.as_view()
    if request.method == 'POST':
        request.POST = request.POST.copy()
        # No es necesario modificar POST, solo pasar empresa en kwargs
        return view(request, empresa=empresa, *args, **kwargs)
    return view(request, empresa=empresa, *args, **kwargs)

def editar_cliente(request, *args, **kwargs):
    log.info("FBV shim: editar_cliente")
    return ClienteUpdateView.as_view()(request, *args, **kwargs)

from taller.models.clientes import Cliente
from django.shortcuts import redirect, get_object_or_404
from django.http import HttpResponse, HttpResponseBadRequest
from django.http import JsonResponse
from django.db.models import Count

def eliminar_cliente(request, cliente_id=None, pk=None, *args, **kwargs):
    """Elimina un cliente (confirmación con diseño futurista).

    Acepta ``cliente_id`` o ``pk`` para compatibilidad retro.
    GET -> muestra confirmación.
    POST -> elimina y redirige.
    """
    target_id = cliente_id or pk
    if target_id is None:
        return HttpResponseBadRequest("Falta parámetro cliente_id / pk")

    cliente = get_object_or_404(Cliente, pk=target_id)
    if request.method == "POST":
        cliente.delete()
        try:
            return redirect("taller:clientes:lista_clientes")
        except Exception:
            return redirect("clientes:lista_clientes")
    from django.shortcuts import render
    return render(request, "taller/clientes/confirmar_eliminacion.html", {"cliente": cliente})


def clientes_stats(request):
    """Return JSON with counts of clients per region."""
    # Optional filters: start_date, end_date (YYYY-MM-DD), country
    start = request.GET.get('start_date')
    end = request.GET.get('end_date')
    country = request.GET.get('country')

    qs = Cliente.objects.all()
    if country:
        qs = qs.filter(empresa__pais__iexact=country)
    if start:
        qs = qs.filter(fecha_creacion__gte=start)
    if end:
        qs = qs.filter(fecha_creacion__lte=end)

    agg = qs.values('region__nombre').annotate(count=Count('id')).order_by('-count')
    labels = [row.get('region__nombre') or 'Sin región' for row in agg]
    counts = [row['count'] for row in agg]
    return JsonResponse({'labels': labels, 'counts': counts})
