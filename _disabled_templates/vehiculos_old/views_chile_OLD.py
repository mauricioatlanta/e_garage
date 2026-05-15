from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from django.shortcuts import redirect, render

from taller.models.clientes import Cliente
from taller.models.extras_vehiculo import ColorVehiculo
from taller.models.marca import Marca
from taller.models.vehiculos import Vehiculo

from .forms import VehiculoForm


@login_required
def lista_vehiculos(request):
    """Vista para listar vehículos en Chile con estadísticas profesionales"""
    # Obtener empresa del usuario
    empresa = getattr(request.user, "empresa", None)

    # Filtrar vehículos por empresa y país Chile
    vehiculos = Vehiculo.objects.filter(empresa=empresa, pais="CL").select_related(
        "cliente", "marca", "modelo", "color"
    )

    # Búsqueda por query - MEJORADA para búsqueda inteligente
    q = request.GET.get("q", "").strip()
    if q:
        # Búsqueda más inteligente con múltiples campos
        search_query = Q()
        search_query |= Q(patente__icontains=q)
        search_query |= Q(vin__icontains=q)
        search_query |= Q(modelo__nombre__icontains=q)
        search_query |= Q(marca__nombre__icontains=q)
        search_query |= Q(cliente__nombre__icontains=q)
        search_query |= Q(cliente__apellido__icontains=q)

        # Búsqueda adicional en campos relacionados
        if q.isdigit():
            # Si es un número, buscar también en año
            search_query |= Q(anio=q)

        vehiculos = vehiculos.filter(search_query)

        # Agregar mensaje de búsqueda
        messages.info(request, f'🔍 Búsqueda: "{q}" - {vehiculos.count()} vehículos encontrados')

    # Estadísticas para el dashboard
    total_vehiculos = vehiculos.count()
    vehiculos_activos = vehiculos.filter(activo=True).count()
    vehiculos_mantenimiento = vehiculos.filter(activo=False).count()

    # Distribución por marca
    distribucion_marcas = (
        vehiculos.values("marca__nombre").annotate(count=Count("id")).order_by("-count")[:5]
    )

    # Distribución por año - CORREGIDO: usar 'anio' en lugar de 'ano'
    distribucion_anios = vehiculos.values("anio").annotate(count=Count("id")).order_by("-anio")[:10]

    context = {
        "vehiculos": vehiculos,
        "total_vehiculos": total_vehiculos,
        "vehiculos_activos": vehiculos_activos,
        "vehiculos_mantenimiento": vehiculos_mantenimiento,
        "distribucion_marcas": distribucion_marcas,
        "distribucion_anios": distribucion_anios,
        "country": "CL",
        "empresa": empresa,
        "search_query": q,  # Agregar query de búsqueda al contexto
    }

    # Handle AJAX requests for real-time search
    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        from django.http import JsonResponse
        from django.template.loader import render_to_string

        # Render only the table content for AJAX
        table_html = render_to_string("taller/common/vehiculos/_table.html", context, request)
        pagination_html = render_to_string(
            "taller/common/vehiculos/_pagination.html", context, request
        )
        empty_state_html = render_to_string(
            "taller/common/vehiculos/_empty_state.html", context, request
        )

        return JsonResponse(
            {
                "table_html": table_html,
                "pagination_html": pagination_html,
                "empty_state_html": empty_state_html,
                "total_count": total_vehiculos,
                "search_query": q,
            }
        )

    return render(request, "taller/cl/es/vehiculos/vehiculo_list.html", context)


@login_required
def crear_vehiculo(request):
    """Formulario creación de vehículo para país CL usando VehiculoForm personalizado."""
    empresa = getattr(request, "empresa", getattr(request.user, "empresa", None))
    if request.method == "POST":
        form = VehiculoForm(request.POST, user=request.user)
        if form.is_valid():
            vehiculo = form.save(commit=False)
            if empresa:
                vehiculo.empresa = empresa
            vehiculo.save()
            messages.success(request, "🚗 Vehículo creado correctamente.")
            return redirect("chile:taller:vehiculos:lista_vehiculos")
    else:
        form = VehiculoForm(user=request.user)
    context = {
        "form": form,
        "country": "CL",
        "clientes": Cliente.objects.filter(empresa=empresa)[:500],  # BLINDAJE: Filtrado por empresa
        "marcas": Marca.objects.filter(country="CL").order_by("nombre"),
        "colores": ColorVehiculo.get_colores_para_pais("CL"),  # CORREGIDO: Colores en español
    }
    return render(request, "taller/vehiculos/crear_vehiculo.html", context)
