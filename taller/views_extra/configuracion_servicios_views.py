# -*- coding: utf-8 -*-
"""
Vista para configurar servicios según los rubros seleccionados por la empresa.
"""
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import redirect, render

from taller.forms.configuracion_forms import ConfiguracionServiciosForm
from taller.models.configuracion import ConfiguracionEmpresa
from taller.servicios.models import ServicioBase
from taller.utils.empresa import get_or_create_empresa


@login_required
def configurar_servicios(request):
    """
    Vista para configurar los rubros de la empresa y gestionar servicios disponibles.

    Permite:
    - Seleccionar múltiples rubros que ofrece el taller
    - Ver servicios disponibles según los rubros seleccionados
    - Ver servicios bloqueados (no relacionados con los rubros seleccionados)
    """
    # Obtener la empresa asociada al usuario autenticado
    empresa = get_or_create_empresa(request)

    # Obtener o crear la configuración de la empresa
    try:
        config_empresa = ConfiguracionEmpresa.objects.get(empresa=empresa)
    except ConfiguracionEmpresa.DoesNotExist:
        config_empresa = ConfiguracionEmpresa.objects.create(empresa=empresa)

    # Determinar idioma
    is_spanish = True
    if hasattr(request, "path"):
        path = request.path
        if "/us/" in path or "/en/" in path:
            is_spanish = False

    if request.method == "POST":
        form = ConfiguracionServiciosForm(request.POST, instance=config_empresa, request=request)
        if form.is_valid():
            form.save()
            if is_spanish:
                messages.success(request, "✅ Rubros y servicios actualizados correctamente.")
            else:
                messages.success(request, "✅ Industry and services updated successfully.")
            return redirect(request.path)
        else:
            if is_spanish:
                messages.error(request, "❌ Por favor corrija los errores en el formulario.")
            else:
                messages.error(request, "❌ Please fix the errors in the form.")
    else:
        form = ConfiguracionServiciosForm(instance=config_empresa, request=request)

    # Obtener rubros seleccionados por la empresa
    rubros_seleccionados = config_empresa.rubros or []

    # Filtrar servicios disponibles según los rubros seleccionados
    # Un servicio está disponible si:
    # 1. Tiene rubros que se solapan con los rubros seleccionados
    # 2. Es genérico (es_generico=True)
    # 3. No tiene rubros definidos (rubros vacío o null)

    servicios_todos = ServicioBase.objects.filter(activo=True).select_related(
        "subcategoria", "subcategoria__categoria"
    )

    if rubros_seleccionados:
        # Filtrar servicios que tienen intersección con los rubros seleccionados
        # Primero obtener todos los servicios activos
        servicios_lista = list(servicios_todos)
        servicios_disponibles_lista = []

        for servicio in servicios_lista:
            # Verificar si el servicio es genérico o no tiene rubros
            if servicio.es_generico or not servicio.rubros or len(servicio.rubros) == 0:
                servicios_disponibles_lista.append(servicio)
                continue

            # Verificar si tiene rubro_sugerido que coincida
            if servicio.rubro_sugerido and servicio.rubro_sugerido in rubros_seleccionados:
                servicios_disponibles_lista.append(servicio)
                continue

            # Verificar si hay intersección entre rubros del servicio y rubros seleccionados
            rubros_servicio = servicio.rubros or []
            if any(rubro in rubros_servicio for rubro in rubros_seleccionados):
                servicios_disponibles_lista.append(servicio)

        # Convertir de vuelta a queryset usando los IDs
        ids_disponibles = [s.id for s in servicios_disponibles_lista]
        servicios_disponibles = servicios_todos.filter(id__in=ids_disponibles)

        # Filtrar servicios bloqueados
        servicios_bloqueados_lista = []
        for servicio in servicios_lista:
            # Excluir genéricos y sin rubros
            if servicio.es_generico or not servicio.rubros or len(servicio.rubros) == 0:
                continue

            # Excluir si tiene rubro_sugerido que coincida
            if servicio.rubro_sugerido and servicio.rubro_sugerido in rubros_seleccionados:
                continue

            # Excluir si hay intersección
            rubros_servicio = servicio.rubros or []
            if any(rubro in rubros_servicio for rubro in rubros_seleccionados):
                continue

            # Si llegamos aquí, el servicio está bloqueado
            servicios_bloqueados_lista.append(servicio)

        ids_bloqueados = [s.id for s in servicios_bloqueados_lista]
        servicios_bloqueados = servicios_todos.filter(id__in=ids_bloqueados)
    else:
        # Si no hay rubros seleccionados, mostrar solo servicios genéricos
        servicios_disponibles = servicios_todos.filter(
            Q(es_generico=True) | Q(rubros__isnull=True) | Q(rubros=[])
        )

        # Todos los no genéricos están bloqueados
        servicios_bloqueados = servicios_todos.filter(es_generico=False).exclude(
            Q(rubros__isnull=True) | Q(rubros=[])
        )

    # Ordenar servicios
    servicios_disponibles = servicios_disponibles.select_related(
        "subcategoria", "subcategoria__categoria"
    ).order_by("subcategoria__categoria__orden", "subcategoria__orden", "nombre")

    servicios_bloqueados = servicios_bloqueados.select_related(
        "subcategoria", "subcategoria__categoria"
    ).order_by("subcategoria__categoria__orden", "subcategoria__orden", "nombre")

    context = {
        "form": form,
        "empresa": empresa,
        "config_empresa": config_empresa,
        "servicios_disponibles": servicios_disponibles,
        "servicios_bloqueados": servicios_bloqueados,
        "rubros_seleccionados": rubros_seleccionados,
        "is_spanish": is_spanish,
    }

    return render(request, "taller/settings/configurar_servicios.html", context)
