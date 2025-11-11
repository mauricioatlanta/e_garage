from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.utils.translation import get_language

from taller.utils.templates import select_country_lang_template

from .models import CategoriaServicio, Servicio, ServicioExterno, SubcategoriaServicio


# Menú principal de servicios con diseño moderno
def servicios_menu(request):
    # Obtener empresa del usuario
    empresa = getattr(request.user, "empresa", None)

    # Obtener país e idioma del request
    country_code = empresa.pais if empresa else "CL"
    lang = get_language() or "es"

    # Obtener servicios con filtros básicos
    servicios = Servicio.objects.filter(empresa=empresa) if empresa else Servicio.objects.none()

    # Filtrar categorías por país
    categorias = CategoriaServicio.objects.filter(country=country_code).prefetch_related("names")
    subcategorias = SubcategoriaServicio.objects.filter(country=country_code).prefetch_related(
        "names"
    )

    # Agrupar servicios por categoría para mejor organización
    servicios_por_categoria = {}
    for categoria in categorias:
        servicios_cat = servicios.filter(categoria=categoria).select_related("subcategoria")
        if servicios_cat.exists():
            servicios_por_categoria[categoria] = servicios_cat

    # Estadísticas para el dashboard
    stats = {
        "total_servicios": servicios.count(),
        "total_categorias": categorias.count(),
        "total_subcategorias": subcategorias.count(),
        "categorias_con_servicios": len(servicios_por_categoria),
    }

    context = {
        "servicios": servicios[:50],  # Limitar para performance inicial
        "servicios_por_categoria": servicios_por_categoria,
        "categorias": categorias,
        "subcategorias": subcategorias,
        "stats": stats,
        "empresa": empresa,
        "country_code": country_code,
        "language": lang,
    }

    # Para usuarios de USA, usar template específico
    if country_code == "US":
        template_name = "taller/us/en/servicios/servicios_menu.html"
    else:
        template_name = select_country_lang_template(
            "servicios/servicios_menu.html", country_code, lang
        )
    return render(request, template_name, context)


# API para búsqueda en tiempo real
def buscar_servicios_api(request):
    query = request.GET.get("q", "").strip()
    categoria_id = request.GET.get("categoria", "")

    # Obtener empresa del usuario
    empresa = getattr(request.user, "empresa", None)

    servicios = Servicio.objects.filter(empresa=empresa) if empresa else Servicio.objects.none()

    # Aplicar filtros de búsqueda
    if query:
        servicios = servicios.filter(
            Q(nombre__icontains=query)
            | Q(categoria__names__label__icontains=query)
            | Q(subcategoria__names__label__icontains=query)
        ).distinct()

    if categoria_id:
        servicios = servicios.filter(categoria_id=categoria_id)

    # Preparar datos para JSON
    data = []
    for servicio in servicios[:20]:  # Limitar resultados
        data.append(
            {
                "pk": servicio.pk,
                "nombre": servicio.nombre,
                "categoria": (servicio.categoria.get_label() if servicio.categoria else ""),
                "subcategoria": (
                    servicio.subcategoria.get_label() if servicio.subcategoria else ""
                ),
            }
        )

    return JsonResponse(
        {
            "servicios": data,
            "total": servicios.count(),
        }
    )


# Menú de otros servicios (placeholder)
def otros_servicios_menu(request):
    """Vista para el menú de otros servicios (servicios externos) con búsqueda inteligente"""

    # Determinar el país basándose en la URL
    country_code = "US" if request.path.startswith("/us/") else "CL"

    # Obtener empresa del usuario
    empresa = getattr(request.user, "empresa", None)
    if empresa:
        # Obtener servicios externos de la empresa
        otros_servicios = ServicioExterno.objects.filter(
            empresa=empresa, activo=True
        ).select_related("categoria", "subcategoria")
    else:
        otros_servicios = ServicioExterno.objects.none()

    # Obtener categorías y subcategorías para el formulario
    categorias = CategoriaServicio.objects.filter(country=country_code)
    subcategorias = SubcategoriaServicio.objects.filter(country=country_code)

    # Estadísticas
    stats = {
        "total_otros_servicios": otros_servicios.count(),
        "total_categorias": otros_servicios.values("categoria").distinct().count(),
        "total_subcategorias": otros_servicios.values("subcategoria").distinct().count(),
        "total_empresas_externas": otros_servicios.values("empresa_externa").distinct().count(),
    }

    # Obtener país e idioma del request
    empresa = getattr(request.user, "empresa", None)
    country_code = empresa.pais if empresa else "CL"

    # Override country detection based on URL path for USA routes
    if request.path.startswith("/us/"):
        country_code = "US"
        lang = "en"
    else:
        lang = get_language() or "es"

    context = {
        "otros_servicios": otros_servicios,
        "categorias": categorias,
        "subcategorias": subcategorias,
        "stats": stats,
        "country": country_code,
        "empresa": empresa,
    }

    template_name = select_country_lang_template(
        "servicios/otros_servicios_menu.html", country_code, lang
    )
    return render(request, template_name, context)


# Crear otro servicio
def crear_otro_servicio(request):
    """Vista para crear servicios externos"""
    from django.contrib import messages
    from django.shortcuts import render

    from taller.servicios.models import CategoriaServicio, ServicioExterno
    from taller.utils.templates import select_country_lang_template

    # Determinar el país basándose en la URL
    country_code = "US" if request.path.startswith("/us/") else "CL"
    lang = "en" if country_code == "US" else "es"

    if request.method == "POST":
        try:
            empresa = getattr(request.user, "empresa", None)
            if not empresa:
                messages.error(request, "Usuario no tiene empresa asociada")
                return redirect("servicios:otros_servicios_menu")

            # Obtener datos del formulario
            nombre = request.POST.get("nombre")
            empresa_externa = request.POST.get("empresa_externa")
            categoria_id = request.POST.get("categoria")
            costo_taller = request.POST.get("costo_taller")
            precio_cliente = request.POST.get("precio_cliente")
            descripcion = request.POST.get("descripcion", "")
            tiempo_estimado = request.POST.get("tiempo_estimado", "")

            # Validaciones básicas
            if not all([nombre, empresa_externa, categoria_id, costo_taller, precio_cliente]):
                messages.error(request, "Todos los campos requeridos deben ser completados")
                return redirect("servicios:otros_servicios_menu")

            # Crear servicio externo
            categoria = CategoriaServicio.objects.get(id=categoria_id)
            servicio = ServicioExterno.objects.create(
                empresa=empresa,
                nombre=nombre,
                empresa_externa=empresa_externa,
                categoria=categoria,
                costo_taller=costo_taller,
                precio_cliente=precio_cliente,
                descripcion=descripcion,
                tiempo_estimado=tiempo_estimado,
                activo=True,
            )

            messages.success(request, f"Servicio externo '{servicio.nombre}' creado exitosamente")

        except Exception as e:
            messages.error(request, f"Error al crear servicio externo: {str(e)}")

        return redirect("taller:servicios:otros_servicios_menu")

    # GET: Mostrar formulario
    categorias = CategoriaServicio.objects.filter(country=country_code)

    # Debug: imprimir categorías encontradas
    print(f"[DEBUG] País: {country_code}")
    print(f"[DEBUG] Categorías encontradas: {categorias.count()}")
    for cat in categorias:
        print(f"[DEBUG] - {cat.id}: {cat.get_label()}")

    context = {
        "categorias": categorias,
        "country": country_code,
    }

    template_name = select_country_lang_template(
        "servicios/crear_otro_servicio.html", country_code, lang
    )

    return render(request, template_name, context)


import logging

log = logging.getLogger(__name__)
from .views_cbv import (
    ServicioCreateView,
    ServicioDetailView,
    ServicioListView,
    ServicioUpdateView,
)


def lista_servicios(request, *args, **kwargs):
    log.info("FBV shim: lista_servicios")
    return ServicioListView.as_view()(request, *args, **kwargs)


def ver_servicio(request, *args, **kwargs):
    log.info("FBV shim: ver_servicio")
    return ServicioDetailView.as_view()(request, *args, **kwargs)


def crear_servicio(request, *args, **kwargs):
    log.info("FBV shim: crear_servicio")
    return ServicioCreateView.as_view()(request, *args, **kwargs)


def editar_servicio(request, *args, **kwargs):
    log.info("FBV shim: editar_servicio")
    return ServicioUpdateView.as_view()(request, *args, **kwargs)
