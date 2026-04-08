from collections import defaultdict

from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import redirect, render

from taller.templatetags.country_url import reverse_country_url
from django.utils.translation import get_language
from django.views.decorators.http import require_POST

from django.contrib.auth.decorators import login_required
from django.utils.text import slugify
import json

from taller.utils.templates import select_country_lang_template

from .models import (
    CategoriaServicio,
    CategoriaServicioName,
    Servicio,
    ServicioExterno,
    SubcategoriaServicio,
    SubcategoriaServicioName,
)

SERVICIO_TYPE_LABELS = {
    "es": {
        "interno": "Interno",
        "externo": "Externo",
        "servicio interno": "Interno",
        "servicio externo": "Externo",
    },
    "en": {
        "interno": "In-shop",
        "externo": "Outsourced",
        "internal": "In-shop",
        "external": "Outsourced",
    },
    "pt": {
        "interno": "Interno",
        "externo": "Externo",
        "serviço interno": "Interno",
        "serviço externo": "Externo",
    },
}


# Menú principal de servicios con diseño moderno
def servicios_menu(request):
    # Obtener empresa del usuario
    empresa = getattr(request.user, "empresa", None)

    # Obtener país e idioma del request
    country_code = _detectar_pais(request)
    lang = get_language() or "es"
    language = COUNTRY_LANGUAGE_MAP.get(country_code, (lang or "es")[:2])

    # Debug: Log para verificar qué país se está detectando
    import logging

    logger = logging.getLogger(__name__)
    logger.info(
        f"servicios_menu - country_code: {country_code}, language: {language}, empresa: {empresa}"
    )

    # Obtener servicios con filtros básicos
    # Primero filtrar por país (importante para mostrar servicios correctos)
    servicios = Servicio.objects.filter(categoria__country=country_code)

    # Debug: Contar servicios antes de filtrar por empresa
    total_servicios_pais = servicios.count()
    logger.info(f"Total servicios para país {country_code}: {total_servicios_pais}")

    # Si el usuario tiene empresa, priorizar servicios de su empresa
    if empresa:
        servicios_empresa = servicios.filter(empresa=empresa)
        servicios_empresa_count = servicios_empresa.count()
        logger.info(f"Servicios de empresa {empresa.id}: {servicios_empresa_count}")
        if servicios_empresa.exists():
            servicios = servicios_empresa
        # Si no tiene servicios en su empresa, mostrar todos del país
        # (ya está filtrado por país arriba)

    servicios_qs = (
        servicios.select_related("categoria", "subcategoria")
        .prefetch_related("names", "categoria__names", "subcategoria__names")
        .order_by("nombre")
    )
    # No filtrar por idioma en los servicios - mostrar todos y localizar después
    servicios_list = list(servicios_qs)
    logger.info(f"Servicios finales en lista: {len(servicios_list)}")

    for servicio in servicios_list:
        servicio.nombre_localizado = servicio.get_label(language)
        servicio.categoria_label = (
            servicio.categoria.get_label(language) if servicio.categoria else ""
        )
        servicio.subcategoria_label = (
            servicio.subcategoria.get_label(language) if servicio.subcategoria else ""
        )
        raw_tipo = (getattr(servicio, "tipo", "") or "").strip().lower()
        servicio.tipo_label = SERVICIO_TYPE_LABELS.get(language, {}).get(
            raw_tipo, raw_tipo.title() if raw_tipo else ""
        )

    # Obtener subcategorías del país primero (para organizarlas por categoría)
    subcategorias_qs = (
        SubcategoriaServicio.objects.filter(country=country_code)
        .prefetch_related("names", "categoria")
        .select_related("categoria")
        .order_by("categoria__code", "code")
        .distinct()
    )

    total_subcategorias_qs = subcategorias_qs.count()
    logger.info(f"Total subcategorías para país {country_code}: {total_subcategorias_qs}")

    subcategorias = []
    subcategorias_por_categoria = defaultdict(list)
    for subcategoria in subcategorias_qs:
        # Obtener nombre localizado (más flexible)
        nombre = subcategoria.get_label(language)
        # Si no hay nombre en el idioma solicitado, intentar con cualquier idioma
        if not nombre or nombre == subcategoria.code:
            # Intentar obtener cualquier nombre disponible
            try:
                any_name = subcategoria.names.first()
                if any_name:
                    nombre = any_name.label
            except:
                nombre = subcategoria.code or f"Subcategory {subcategoria.id}"

        subcategoria.label_localizado = nombre
        subcategorias.append(subcategoria)
        # Organizar subcategorías por categoría
        if subcategoria.categoria:
            subcategorias_por_categoria[subcategoria.categoria].append(subcategoria)

    # Obtener categorías del país, asegurando que tengan nombres en el idioma correcto
    categorias_qs = (
        CategoriaServicio.objects.filter(country=country_code)
        .prefetch_related("names")
        .order_by("code")
        .distinct()
    )

    total_categorias_qs = categorias_qs.count()
    logger.info(f"Total categorías para país {country_code}: {total_categorias_qs}")

    categorias = []
    for categoria in categorias_qs:
        # Obtener nombre localizado (más flexible)
        nombre = categoria.get_label(language)
        # Si no hay nombre en el idioma solicitado, intentar con cualquier idioma
        if not nombre or nombre == categoria.code:
            # Intentar obtener cualquier nombre disponible
            try:
                any_name = categoria.names.first()
                if any_name:
                    nombre = any_name.label
            except:
                nombre = categoria.code or f"Category {categoria.id}"

        categoria.label_localizado = nombre
        # Attach subcategorias to categoria for template access
        categoria.subcategorias_list = subcategorias_por_categoria.get(categoria, [])
        categorias.append(categoria)

    servicios_por_categoria = defaultdict(list)
    for servicio in servicios_list:
        if servicio.categoria and servicio.categoria.country == country_code:
            servicios_por_categoria[servicio.categoria].append(servicio)

    stats = {
        "total_servicios": len(servicios_list),
        "total_categorias": len(categorias),
        "total_subcategorias": len(subcategorias),
        "categorias_con_servicios": sum(1 for items in servicios_por_categoria.values() if items),
    }

    # Debug info
    debug_info = {
        "country_code": country_code,
        "language": language,
        "total_servicios_raw": total_servicios_pais,
        "total_categorias_raw": total_categorias_qs,
        "total_subcategorias_raw": total_subcategorias_qs,
        "empresa_id": empresa.id if empresa else None,
    }
    logger.info(f"Stats finales: {stats}")
    logger.info(f"Debug info: {debug_info}")

    context = {
        "servicios": servicios_list[:50],  # Limitar para performance inicial
        "servicios_por_categoria": servicios_por_categoria,
        "categorias": categorias,
        "subcategorias": subcategorias,
        "subcategorias_por_categoria": subcategorias_por_categoria,
        "stats": stats,
        "empresa": empresa,
        "country_code": country_code,
        "language": language,
        "debug_info": debug_info,  # Para debugging en template
    }

    # Para usuarios de USA, usar template específico
    if country_code == "US":
        template_name = "us/en/servicios/servicios_menu.html"
    else:
        template_name = select_country_lang_template(
            "servicios/servicios_menu.html", country_code, lang
        )
    return render(request, template_name, context)


# API para búsqueda en tiempo real
def buscar_servicios_api(request):
    query = (request.GET.get("q") or "").strip()
    categoria_code = request.GET.get("categoria") or ""
    subcategoria_code = request.GET.get("subcategoria") or ""

    # Obtener empresa del usuario
    empresa = getattr(request.user, "empresa", None)

    if empresa:
        servicios = Servicio.objects.filter(empresa=empresa)
        if not servicios.exists():
            servicios = Servicio.objects.all()
    else:
        servicios = Servicio.objects.all()

    country = _detectar_pais(request)
    language = COUNTRY_LANGUAGE_MAP.get(country, "es")

    # Aplicar filtros de búsqueda
    if query:
        servicios = servicios.filter(
            Q(names__label__icontains=query, names__language=language)
            | Q(categoria__names__label__icontains=query, categoria__names__language=language)
            | Q(subcategoria__names__label__icontains=query, subcategoria__names__language=language)
        ).distinct()

    if categoria_code:
        servicios = servicios.filter(categoria__code=categoria_code)

    if subcategoria_code:
        servicios = servicios.filter(subcategoria__code=subcategoria_code)

    # Preparar datos para JSON
    data = []
    servicios = servicios.select_related("categoria", "subcategoria").prefetch_related(
        "names", "categoria__names", "subcategoria__names"
    )
    servicios = servicios.filter(names__language=language).distinct()
    for servicio in servicios[:20]:  # Limitar resultados
        nombre_localizado = servicio.get_label(language)
        data.append(
            {
                "pk": servicio.pk,
                "nombre": nombre_localizado,
                "categoria": servicio.categoria.get_label(language) if servicio.categoria else "",
                "categoria_id": servicio.categoria_id,
                "categoria_code": servicio.categoria.code if servicio.categoria else "",
                "subcategoria": (
                    servicio.subcategoria.get_label(language) if servicio.subcategoria else ""
                ),
                "subcategoria_id": servicio.subcategoria_id,
                "subcategoria_code": servicio.subcategoria.code if servicio.subcategoria else "",
                "tipo": SERVICIO_TYPE_LABELS.get(language, {}).get(
                    (getattr(servicio, "tipo", "") or "").strip().lower(),
                    (getattr(servicio, "tipo", "") or "").strip().title(),
                ),
            }
        )

    return JsonResponse(
        {
            "servicios": data,
            "total": servicios.count(),
        }
    )


# =================== Endpoints de creación rápida ===================
COUNTRY_LANGUAGE_MAP = {
    "CL": "es",
    "MX": "es",
    "VE": "es",
    "PE": "es",
    "US": "en",
    "BR": "pt",
}

OTHER_LABELS = {
    "CL": {
        "title": "Otros servicios",
        "subtitle": "Servicios gestionados con empresas externas de confianza.",
        "button_add": "Registrar servicio externo",
        "search_placeholder": "Buscar por servicio o proveedor externo...",
        "stats_total": "Servicios externos registrados",
        "stats_providers": "Empresas externas activas",
        "card_service": "Servicio",
        "card_company": "Proveedor externo",
        "card_cost": "Costo al taller",
        "card_price": "Precio al cliente",
        "counter_single": "1 servicio encontrado",
        "counter_plural": "{n} servicios encontrados",
        "empty_title": "Sin servicios externos",
        "empty_message": "Registra tus servicios tercerizados para mantener el control del taller.",
    },
    "MX": {
        "title": "Otros servicios",
        "subtitle": "Trabajos gestionados con proveedores externos de confianza.",
        "button_add": "Registrar servicio externo",
        "search_placeholder": "Busca por servicio o empresa proveedora...",
        "stats_total": "Servicios externos registrados",
        "stats_providers": "Proveedores externos activos",
        "card_service": "Servicio",
        "card_company": "Empresa proveedora",
        "card_cost": "Costo al taller",
        "card_price": "Precio al cliente",
        "counter_single": "1 servicio encontrado",
        "counter_plural": "{n} servicios encontrados",
        "empty_title": "Sin servicios externos",
        "empty_message": "Agrega los servicios tercerizados para tenerlos controlados.",
    },
    "PE": {
        "title": "Otros servicios",
        "subtitle": "Servicios realizados por empresas externas aliadas.",
        "button_add": "Registrar servicio externo",
        "search_placeholder": "Buscar por servicio o proveedor externo...",
        "stats_total": "Servicios externos registrados",
        "stats_providers": "Empresas externas activas",
        "card_service": "Servicio",
        "card_company": "Proveedor externo",
        "card_cost": "Costo al taller",
        "card_price": "Precio al cliente",
        "counter_single": "1 servicio encontrado",
        "counter_plural": "{n} servicios encontrados",
        "empty_title": "Sin servicios externos",
        "empty_message": "Registra tus servicios tercerizados para mantener el control.",
    },
    "VE": {
        "title": "Otros servicios",
        "subtitle": "Trabajos coordinados con aliados externos.",
        "button_add": "Registrar servicio externo",
        "search_placeholder": "Buscar por servicio o proveedor externo...",
        "stats_total": "Servicios externos registrados",
        "stats_providers": "Aliados externos activos",
        "card_service": "Servicio",
        "card_company": "Proveedor externo",
        "card_cost": "Costo al taller",
        "card_price": "Precio al cliente",
        "counter_single": "1 servicio encontrado",
        "counter_plural": "{n} servicios encontrados",
        "empty_title": "Sin servicios externos",
        "empty_message": "Comienza registrando los servicios prestados por terceros.",
    },
    "US": {
        "title": "External services",
        "subtitle": "Jobs handled by trusted third-party vendors.",
        "button_add": "Register external service",
        "search_placeholder": "Search by service or vendor...",
        "stats_total": "External services on record",
        "stats_providers": "Active partner vendors",
        "card_service": "Service",
        "card_company": "Vendor",
        "card_cost": "Cost to shop",
        "card_price": "Price to customer",
        "counter_single": "1 service found",
        "counter_plural": "{n} services found",
        "empty_title": "No external services yet",
        "empty_message": "Log outsourced work to keep your workshop fully tracked.",
    },
    "BR": {
        "title": "Serviços externos",
        "subtitle": "Serviços executados por empresas parceiras confiáveis.",
        "button_add": "Cadastrar serviço externo",
        "search_placeholder": "Buscar por serviço ou empresa parceira...",
        "stats_total": "Serviços externos cadastrados",
        "stats_providers": "Empresas parceiras ativas",
        "card_service": "Serviço",
        "card_company": "Empresa parceira",
        "card_cost": "Custo para a oficina",
        "card_price": "Preço para o cliente",
        "counter_single": "1 serviço encontrado",
        "counter_plural": "{n} serviços encontrados",
        "empty_title": "Sem serviços externos",
        "empty_message": "Cadastre os serviços terceirizados para manter o controle da oficina.",
    },
}

CURRENCY_SETTINGS = {
    "CL": {"code": "CLP", "locale": "es-CL", "symbol": "$"},
    "MX": {"code": "MXN", "locale": "es-MX", "symbol": "$"},
    "PE": {"code": "PEN", "locale": "es-PE", "symbol": "S/"},
    "VE": {"code": "VES", "locale": "es-VE", "symbol": "Bs."},
    "US": {"code": "USD", "locale": "en-US", "symbol": "$"},
    "BR": {"code": "BRL", "locale": "pt-BR", "symbol": "R$"},
}


def _detectar_pais(request):
    empresa = getattr(request.user, "empresa", None)
    if empresa and getattr(empresa, "pais", None):
        return empresa.pais.strip().upper()
    path = request.path.lower()
    if path.startswith("/us/"):
        return "US"
    if path.startswith("/br/"):
        return "BR"
    if path.startswith("/mx/"):
        return "MX"
    if path.startswith("/ve/"):
        return "VE"
    if path.startswith("/pe/"):
        return "PE"
    return "CL"


def _generar_code(nombre, existente_qs):
    base = slugify(nombre) or "categoria"
    code = base.upper().replace("-", "_")
    candidate = code
    idx = 1
    while existente_qs.filter(code=candidate).exists():
        candidate = f"{code}_{idx}"
        idx += 1
    return candidate


@login_required
@require_POST
def crear_categoria_api(request):
    try:
        payload = json.loads(request.body.decode("utf-8"))
    except json.JSONDecodeError:
        return JsonResponse({"success": False, "error": "Datos inválidos"}, status=400)

    nombre = (payload.get("nombre") or "").strip()
    aliases = payload.get("aliases") or []

    if not nombre:
        return JsonResponse({"success": False, "error": "El nombre es obligatorio"}, status=400)

    country = _detectar_pais(request)
    language = COUNTRY_LANGUAGE_MAP.get(country, "es")

    qs = CategoriaServicio.objects.filter(country=country)
    code = _generar_code(nombre, qs)

    categoria, created = CategoriaServicio.objects.get_or_create(
        country=country,
        code=code,
    )

    CategoriaServicioName.objects.update_or_create(
        categoria=categoria,
        language=language,
        is_default=True,
        defaults={
            "label": nombre,
            "aliases": aliases if isinstance(aliases, list) else [aliases],
        },
    )

    return JsonResponse(
        {
            "success": True,
            "categoria": {
                "id": categoria.id,
                "code": categoria.code,
                "label": nombre,
                "country": categoria.country,
            },
            "created": created,
        }
    )


@login_required
@require_POST
def crear_subcategoria_api(request):
    try:
        payload = json.loads(request.body.decode("utf-8"))
    except json.JSONDecodeError:
        return JsonResponse({"success": False, "error": "Datos inválidos"}, status=400)

    categoria_id = payload.get("categoria_id")
    nombre = (payload.get("nombre") or "").strip()
    aliases = payload.get("aliases") or []

    if not categoria_id or not nombre:
        return JsonResponse(
            {"success": False, "error": "Debe seleccionar categoria y nombre"}, status=400
        )

    try:
        categoria = CategoriaServicio.objects.get(pk=categoria_id)
    except CategoriaServicio.DoesNotExist:
        return JsonResponse({"success": False, "error": "Categoría no encontrada"}, status=404)

    country = categoria.country
    language = COUNTRY_LANGUAGE_MAP.get(country, "es")

    qs = SubcategoriaServicio.objects.filter(categoria=categoria)
    code = _generar_code(nombre, qs)

    subcategoria, created = SubcategoriaServicio.objects.get_or_create(
        categoria=categoria,
        code=code,
        defaults={"country": country},
    )
    subcategoria.country = country
    subcategoria.save(update_fields=["country"])

    SubcategoriaServicioName.objects.update_or_create(
        subcategoria=subcategoria,
        language=language,
        is_default=True,
        defaults={
            "label": nombre,
            "aliases": aliases if isinstance(aliases, list) else [aliases],
        },
    )

    return JsonResponse(
        {
            "success": True,
            "subcategoria": {
                "id": subcategoria.id,
                "code": subcategoria.code,
                "label": nombre,
                "categoria_id": categoria.id,
            },
            "created": created,
        }
    )


@login_required
def buscar_otros_servicios_api(request):
    empresa = getattr(request.user, "empresa", None)
    if not empresa:
        return JsonResponse({"otros_servicios": [], "total": 0})

    country = _detectar_pais(request)
    language = COUNTRY_LANGUAGE_MAP.get(country, "es")

    if empresa:
        otros_servicios = (
            ServicioExterno.objects.filter(empresa=empresa)
            .select_related("categoria", "subcategoria")
            .order_by("nombre")
        )
        if not otros_servicios.exists():
            otros_servicios = (
                ServicioExterno.objects.all()
                .select_related("categoria", "subcategoria")
                .order_by("nombre")
            )
    else:
        otros_servicios = (
            ServicioExterno.objects.all()
            .select_related("categoria", "subcategoria")
            .order_by("nombre")
        )

    query = (request.GET.get("q") or "").strip()
    if query:
        otros_servicios = otros_servicios.filter(
            Q(nombre__icontains=query) | Q(empresa_externa__icontains=query)
        )

    categoria_code = request.GET.get("categoria") or ""
    if categoria_code:
        otros_servicios = otros_servicios.filter(categoria__code=categoria_code)

    subcategoria_code = request.GET.get("subcategoria") or ""
    if subcategoria_code:
        otros_servicios = otros_servicios.filter(subcategoria__code=subcategoria_code)

    data = []
    for servicio in otros_servicios[:20]:
        data.append(
            {
                "pk": servicio.pk,
                "nombre": servicio.nombre,
                "empresa_externa": servicio.empresa_externa,
                "categoria": servicio.categoria.get_label(language) if servicio.categoria else "",
                "categoria_id": servicio.categoria_id,
                "categoria_code": servicio.categoria.code if servicio.categoria else "",
                "subcategoria": (
                    servicio.subcategoria.get_label(language) if servicio.subcategoria else ""
                ),
                "subcategoria_id": servicio.subcategoria_id,
                "subcategoria_code": servicio.subcategoria.code if servicio.subcategoria else "",
                "costo_taller": str(servicio.costo_taller),
                "precio_cliente": str(servicio.precio_cliente),
            }
        )

    return JsonResponse({"otros_servicios": data, "total": otros_servicios.count()})


# Menú de otros servicios (placeholder)
@login_required
def otros_servicios_menu(request):
    """Vista para el menú de otros servicios (servicios externos) con búsqueda inteligente"""

    empresa = getattr(request.user, "empresa", None)
    country_code = _detectar_pais(request)
    # Detectar idioma real del request, no solo el mapeo por país
    language = (
        get_language()
        or getattr(request, "LANGUAGE_CODE", None)
        or COUNTRY_LANGUAGE_MAP.get(country_code, "es")
    )
    # Si el idioma es español, usar labels de CL (que están en español)
    # Si el idioma es inglés y el país es US, usar labels de US
    if language == "es":
        labels = OTHER_LABELS.get("CL", OTHER_LABELS["CL"])
    elif country_code == "US" and language == "en":
        labels = OTHER_LABELS.get("US", OTHER_LABELS["CL"])
    else:
        labels = OTHER_LABELS.get(country_code, OTHER_LABELS["CL"])
    currency_settings = CURRENCY_SETTINGS.get(country_code, CURRENCY_SETTINGS["CL"])

    if empresa:
        otros_qs = (
            ServicioExterno.objects.filter(empresa=empresa)
            .select_related("categoria", "subcategoria")
            .order_by("nombre")
        )
    else:
        otros_qs = ServicioExterno.objects.none()

    categorias = (
        CategoriaServicio.objects.filter(country=country_code)
        .prefetch_related("names")
        .order_by("code")
    )
    subcategorias = (
        SubcategoriaServicio.objects.filter(country=country_code)
        .prefetch_related("names")
        .order_by("code")
    )

    stats = {
        "total_servicios": otros_qs.count(),
        "total_proveedores": otros_qs.values("empresa_externa").distinct().count(),
        "total_categorias": categorias.count(),
    }

    otros_servicios = list(otros_qs[:50])
    otros_servicios_data = []
    for servicio in otros_servicios:
        otros_servicios_data.append(
            {
                "pk": servicio.pk,
                "nombre": servicio.nombre,
                "empresa_externa": servicio.empresa_externa or "",
                "categoria": servicio.categoria.get_label(language) if servicio.categoria else "",
                "categoria_id": servicio.categoria_id,
                "categoria_code": servicio.categoria.code if servicio.categoria else "",
                "subcategoria": (
                    servicio.subcategoria.get_label(language) if servicio.subcategoria else ""
                ),
                "subcategoria_id": servicio.subcategoria_id,
                "subcategoria_code": servicio.subcategoria.code if servicio.subcategoria else "",
                "costo_taller": str(servicio.costo_taller),
                "precio_cliente": str(servicio.precio_cliente),
            }
        )

    context = {
        "otros_servicios": otros_servicios_data,
        "categorias": categorias,
        "subcategorias": subcategorias,
        "stats": stats,
        "labels": labels,
        "country": country_code,
        "language": language,
        "currency_settings": currency_settings,
        "empresa": empresa,
    }

    template_name = select_country_lang_template(
        "servicios/otros_servicios_menu.html", country_code, language
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
            from taller.common.mixins.return_to_document import build_return_to_document_url

            empresa = getattr(request.user, "empresa", None)
            if not empresa:
                messages.error(request, "Usuario no tiene empresa asociada")
                return redirect(reverse_country_url(request, "servicios:otros_servicios_menu"))

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
                return redirect(reverse_country_url(request, "servicios:otros_servicios_menu"))

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
            return_to = (
                request.POST.get("return_to")
                or request.GET.get("return_to")
                or request.POST.get("next")
                or request.GET.get("next")
                or ""
            ).strip()
            if return_to:
                redirect_url = build_return_to_document_url(
                    request,
                    entity_type="otro_servicio",
                    field_target=(
                        request.POST.get("field_target")
                        or request.GET.get("field_target")
                        or "otro_servicio"
                    ),
                    created_id=servicio.id,
                    created_label=servicio.nombre or f"Servicio externo #{servicio.id}",
                )
                return redirect(redirect_url)

        except Exception as e:
            messages.error(request, f"Error al crear servicio externo: {str(e)}")

        return redirect(reverse_country_url(request, "servicios:otros_servicios_menu"))

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


@login_required
def editar_otro_servicio(request, pk):
    """Vista para editar servicios externos"""
    from django.contrib import messages
    from django.shortcuts import get_object_or_404, redirect, render

    from taller.servicios.models import CategoriaServicio, ServicioExterno
    from taller.utils.templates import select_country_lang_template

    servicio = get_object_or_404(
        ServicioExterno, pk=pk, empresa=getattr(request.user, "empresa", None)
    )

    # Determinar el país basándose en la URL
    country_code = _detectar_pais(request)
    lang = get_language() or COUNTRY_LANGUAGE_MAP.get(country_code, "es")

    if request.method == "POST":
        try:
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
                return redirect(
                    reverse_country_url(request, "servicios:editar_otro_servicio", pk=pk)
                )

            # Actualizar servicio externo
            categoria = CategoriaServicio.objects.get(id=categoria_id)
            servicio.nombre = nombre
            servicio.empresa_externa = empresa_externa
            servicio.categoria = categoria
            servicio.costo_taller = costo_taller
            servicio.precio_cliente = precio_cliente
            servicio.descripcion = descripcion
            servicio.tiempo_estimado = tiempo_estimado
            servicio.save()

            messages.success(
                request, f"Servicio externo '{servicio.nombre}' actualizado exitosamente"
            )
            return redirect(reverse_country_url(request, "servicios:otros_servicios_menu"))

        except Exception as e:
            messages.error(request, f"Error al actualizar servicio externo: {str(e)}")

    # GET: Mostrar formulario
    categorias = CategoriaServicio.objects.filter(country=country_code)

    context = {
        "servicio": servicio,
        "categorias": categorias,
        "country": country_code,
    }

    template_name = select_country_lang_template(
        "servicios/editar_otro_servicio.html", country_code, lang
    )

    return render(request, template_name, context)


@login_required
@require_POST
@login_required
def eliminar_otro_servicio(request, pk):
    """Vista para eliminar servicios externos - FILTRADO POR EMPRESA"""
    from django.contrib import messages
    from django.shortcuts import get_object_or_404, redirect

    from taller.servicios.models import ServicioExterno

    # 🔒 BLINDAJE MULTI-TENANT: Verificar empresa antes de buscar
    empresa = getattr(request.user, "empresa", None)
    if not empresa:
        messages.error(request, "Usuario sin empresa asignada")
        return redirect(reverse_country_url(request, "servicios:otros_servicios_menu"))

    servicio = get_object_or_404(ServicioExterno, pk=pk, empresa=empresa)
    nombre_servicio = servicio.nombre
    servicio.delete()

    messages.success(request, f"Servicio externo '{nombre_servicio}' eliminado exitosamente")
    return redirect(reverse_country_url(request, "servicios:otros_servicios_menu"))


import logging

log = logging.getLogger(__name__)
from .views_cbv import (
    ServicioCreateView,
    ServicioDeleteView,
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


def eliminar_servicio(request, *args, **kwargs):
    """Vista para eliminar un servicio"""
    log.info("FBV shim: eliminar_servicio")
    return ServicioDeleteView.as_view()(request, *args, **kwargs)
