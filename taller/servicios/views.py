from django.db.models import Q
from django.http import JsonResponse
from django.core.cache import cache
from django.middleware.csrf import get_token
from django.shortcuts import redirect, render

from taller.templatetags.country_url import reverse_country_url
from django.utils.translation import get_language, gettext as _
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


SERVICIOS_MENU_UI_LABELS = {
    "es": {
        "deleteConfirm": "¿Seguro que deseas eliminar este servicio?",
        "deleteError": "No se pudo eliminar el servicio.",
        "searchError": "No se pudo actualizar el listado.",
        "emptyTitle": "No se encontraron servicios",
        "emptyMessage": "Ajusta los filtros o crea un nuevo servicio.",
        "loading": "Cargando servicios...",
        "resultsSingle": "1 servicio encontrado",
        "resultsPluralSuffix": "servicios encontrados",
    },
    "en": {
        "deleteConfirm": "Are you sure you want to delete this service?",
        "deleteError": "The service could not be deleted.",
        "searchError": "The list could not be updated.",
        "emptyTitle": "No services found",
        "emptyMessage": "Adjust the filters or create a new service.",
        "loading": "Loading services...",
        "resultsSingle": "1 service found",
        "resultsPluralSuffix": "services found",
    },
    "pt": {
        "deleteConfirm": "Tem certeza de que deseja excluir este servico?",
        "deleteError": "Nao foi possivel excluir o servico.",
        "searchError": "Nao foi possivel atualizar a lista.",
        "emptyTitle": "Nenhum servico encontrado",
        "emptyMessage": "Ajuste os filtros ou crie um novo servico.",
        "loading": "Carregando servicos...",
        "resultsSingle": "1 servico encontrado",
        "resultsPluralSuffix": "servicos encontrados",
    },
}


def _safe_reverse_country_url(request, view_path, fallback="#", *args, **kwargs):
    try:
        return reverse_country_url(request, view_path, *args, **kwargs)
    except Exception:
        return fallback


def _resolve_servicios_menu_scope(request):
    empresa = getattr(request.user, "empresa", None)
    country_code = _detectar_pais(request)
    request_lang = get_language() or getattr(request, "LANGUAGE_CODE", None) or "es"
    language = COUNTRY_LANGUAGE_MAP.get(country_code, (request_lang or "es")[:2])

    servicios_pais = Servicio.objects.filter(categoria__country=country_code)
    total_servicios_pais = servicios_pais.count()

    servicios_qs = servicios_pais
    servicios_empresa_count = 0
    if empresa:
        servicios_empresa = servicios_pais.filter(empresa=empresa)
        servicios_empresa_count = servicios_empresa.count()
        if servicios_empresa_count:
            servicios_qs = servicios_empresa

    servicios_qs = (
        servicios_qs.select_related("categoria", "subcategoria")
        .prefetch_related("names", "categoria__names", "subcategoria__names")
        .order_by("categoria__orden", "subcategoria__orden", "nombre")
    )

    return {
        "empresa": empresa,
        "country_code": country_code,
        "language": language,
        "servicios_qs": servicios_qs,
        "total_servicios_pais": total_servicios_pais,
        "servicios_empresa_count": servicios_empresa_count,
    }


def _localize_taxonomy_label(item, language, fallback_prefix):
    nombre = item.get_label(language)
    if nombre and nombre != item.code:
        return nombre

    try:
        any_name = item.names.first()
        if any_name:
            return any_name.label
    except Exception:
        pass

    return item.code or f"{fallback_prefix} {item.id}"


def _get_servicios_filters(country_code, language):
    categorias_qs = (
        CategoriaServicio.objects.filter(country=country_code)
        .prefetch_related("names")
        .order_by("orden", "code")
    )
    subcategorias_qs = (
        SubcategoriaServicio.objects.filter(country=country_code)
        .select_related("categoria")
        .prefetch_related("names")
        .order_by("categoria__orden", "orden", "code")
    )

    categorias = [
        {
            "code": categoria.code or "",
            "label": _localize_taxonomy_label(categoria, language, "Category"),
        }
        for categoria in categorias_qs
    ]
    subcategorias = [
        {
            "code": subcategoria.code or "",
            "label": _localize_taxonomy_label(subcategoria, language, "Subcategory"),
            "categoria_code": subcategoria.categoria.code if subcategoria.categoria else "",
        }
        for subcategoria in subcategorias_qs
    ]

    return {
        "categorias": categorias,
        "subcategorias": subcategorias,
    }


def _serialize_servicio_menu_item(request, servicio, language):
    raw_tipo = (getattr(servicio, "tipo", "") or "").strip().lower()
    return {
        "id": servicio.pk,
        "nombre": servicio.get_label(language),
        "descripcion": servicio.descripcion or "",
        "codigo_interno": servicio.codigo_interno or "",
        "categoria": servicio.categoria.get_label(language) if servicio.categoria else "",
        "categoria_code": servicio.categoria.code if servicio.categoria else "",
        "subcategoria": servicio.subcategoria.get_label(language) if servicio.subcategoria else "",
        "subcategoria_code": servicio.subcategoria.code if servicio.subcategoria else "",
        "tipo": SERVICIO_TYPE_LABELS.get(language, {}).get(
            raw_tipo, raw_tipo.title() if raw_tipo else ""
        )
        or _("Interno"),
        "view_url": _safe_reverse_country_url(request, "servicios:ver_servicio", "#", servicio.pk),
        "edit_url": _safe_reverse_country_url(
            request, "servicios:editar_servicio", "#", servicio.pk
        ),
        "delete_url": _safe_reverse_country_url(
            request, "servicios:eliminar_servicio", "#", servicio.pk
        ),
    }


def _get_servicios_menu_ui_labels(language):
    return SERVICIOS_MENU_UI_LABELS.get(language, SERVICIOS_MENU_UI_LABELS["es"]).copy()


# Menú principal de servicios con diseño moderno
def servicios_menu(request):
    import logging

    logger = logging.getLogger(__name__)
    scope = _resolve_servicios_menu_scope(request)
    empresa = scope["empresa"]
    country_code = scope["country_code"]
    language = scope["language"]
    filters = _get_servicios_filters(country_code, language)

    logger.info(
        f"servicios_menu - country_code: {country_code}, language: {language}, empresa: {empresa}"
    )
    stats = {
        "total_servicios": scope["servicios_qs"].count(),
        "total_categorias": len(filters["categorias"]),
        "total_subcategorias": len(filters["subcategorias"]),
    }

    debug_info = {
        "country_code": country_code,
        "language": language,
        "total_servicios_raw": scope["total_servicios_pais"],
        "servicios_empresa_raw": scope["servicios_empresa_count"],
        "empresa_id": empresa.id if empresa else None,
    }
    logger.info(f"Stats finales: {stats}")
    logger.info(f"Debug info: {debug_info}")

    dashboard_url = _safe_reverse_country_url(request, "dashboard", "/")
    servicios_menu_url = _safe_reverse_country_url(
        request, "servicios:servicios_menu", request.path
    )
    servicios_data_url = _safe_reverse_country_url(
        request, "servicios:servicios_menu_data_api", request.path
    )
    create_url = _safe_reverse_country_url(request, "servicios:crear_servicio", "#")

    context = {
        "categorias": filters["categorias"],
        "subcategorias": filters["subcategorias"],
        "stats": stats,
        "empresa": empresa,
        "country_code": country_code,
        "language": language,
        "debug_info": debug_info,
        "dashboard_url": dashboard_url,
        "create_url": create_url,
        "servicios_menu_config": {
            "dataUrl": servicios_data_url,
            "menuUrl": servicios_menu_url,
            "dashboardUrl": dashboard_url,
            "createUrl": create_url,
            "csrfToken": get_token(request),
            "labels": _get_servicios_menu_ui_labels(language),
        },
    }

    return render(request, "taller/common/servicios/servicios_menu_shell.html", context)


def servicios_menu_data_api(request):
    query = (request.GET.get("q") or "").strip()
    categoria_code = request.GET.get("categoria") or ""
    subcategoria_code = request.GET.get("subcategoria") or ""

    try:
        limit = int(request.GET.get("limit", 24))
    except (TypeError, ValueError):
        limit = 24
    limit = max(1, min(limit, 60))

    scope = _resolve_servicios_menu_scope(request)
    servicios = scope["servicios_qs"]
    language = scope["language"]
    empresa = scope["empresa"]
    country = scope["country_code"]

    cache_key = f"servicios_menu:{empresa.id if empresa else 0}:{country}:{language}:{query}:{categoria_code}:{subcategoria_code}:{limit}"

    cached = cache.get(cache_key)
    if cached:
        return JsonResponse(cached)

    if query:
        servicios = servicios.filter(
            Q(nombre__icontains=query)
            | Q(descripcion__icontains=query)
            | Q(codigo_interno__icontains=query)
            | Q(names__label__icontains=query, names__language=language)
            | Q(names__aliases__icontains=query)
            | Q(categoria__names__label__icontains=query, categoria__names__language=language)
            | Q(subcategoria__names__label__icontains=query, subcategoria__names__language=language)
        ).distinct()

    if categoria_code:
        servicios = servicios.filter(categoria__code=categoria_code)

    if subcategoria_code:
        servicios = servicios.filter(subcategoria__code=subcategoria_code)

    total = servicios.count()
    data = [
        _serialize_servicio_menu_item(request, servicio, language) for servicio in servicios[:limit]
    ]

    result = {"servicios": data, "total": total}

    cache.set(cache_key, result, 300)

    return JsonResponse(result)


# API para búsqueda en tiempo real
def buscar_servicios_api(request):
    query = (request.GET.get("q") or "").strip()
    categoria_code = request.GET.get("categoria") or ""
    subcategoria_code = request.GET.get("subcategoria") or ""

    # Obtener empresa del usuario
    empresa = getattr(request.user, "empresa", None)

    if not empresa:
        return JsonResponse({"servicios": [], "total": 0})

    servicios = (
        Servicio.objects.filter(empresa=empresa, activo=True)
        .select_related("categoria", "subcategoria")
        .prefetch_related("names", "categoria__names", "subcategoria__names")
    )

    country = _detectar_pais(request)
    language = COUNTRY_LANGUAGE_MAP.get(country, "es")

    # Aplicar filtros de búsqueda
    if query:
        servicios = servicios.filter(
            Q(nombre__icontains=query)
            | Q(descripcion__icontains=query)
            | Q(codigo_interno__icontains=query)
            | Q(names__label__icontains=query, names__language=language)
            | Q(names__aliases__icontains=query)
            | Q(categoria__names__label__icontains=query, categoria__names__language=language)
            | Q(subcategoria__names__label__icontains=query, subcategoria__names__language=language)
        ).distinct()

    if categoria_code:
        servicios = servicios.filter(categoria__code=categoria_code)

    if subcategoria_code:
        servicios = servicios.filter(subcategoria__code=subcategoria_code)

    total = servicios.count()

    # Preparar datos para JSON
    data = []
    for servicio in servicios.order_by("categoria__orden", "subcategoria__orden", "nombre")[:20]:
        nombre_localizado = servicio.get_label(language)
        precio_base = servicio.precio_base or 0
        data.append(
            {
                "id": servicio.pk,
                "pk": servicio.pk,
                "nombre": nombre_localizado,
                "label": nombre_localizado,
                "text": nombre_localizado,
                "descripcion": servicio.descripcion or "",
                "codigo_interno": servicio.codigo_interno or "",
                "categoria": servicio.categoria.get_label(language) if servicio.categoria else "",
                "categoria_id": servicio.categoria_id,
                "categoria_code": servicio.categoria.code if servicio.categoria else "",
                "subcategoria": (
                    servicio.subcategoria.get_label(language) if servicio.subcategoria else ""
                ),
                "subcategoria_id": servicio.subcategoria_id,
                "subcategoria_code": servicio.subcategoria.code if servicio.subcategoria else "",
                "precio": str(precio_base),
                "precio_base": str(precio_base),
                "tipo": SERVICIO_TYPE_LABELS.get(language, {}).get(
                    (getattr(servicio, "tipo", "") or "").strip().lower(),
                    (getattr(servicio, "tipo", "") or "").strip().title(),
                ),
            }
        )

    return JsonResponse(
        {
            "servicios": data,
            "total": total,
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
        precio_taller = servicio.costo_taller or 0
        precio_cliente = servicio.precio_cliente or 0
        data.append(
            {
                "id": servicio.pk,
                "pk": servicio.pk,
                "nombre": servicio.nombre,
                "label": servicio.nombre,
                "text": servicio.nombre,
                "empresa": servicio.empresa_externa,
                "empresa_ext": servicio.empresa_externa,
                "empresa_externa": servicio.empresa_externa,
                "categoria": servicio.categoria.get_label(language) if servicio.categoria else "",
                "categoria_id": servicio.categoria_id,
                "categoria_code": servicio.categoria.code if servicio.categoria else "",
                "subcategoria": (
                    servicio.subcategoria.get_label(language) if servicio.subcategoria else ""
                ),
                "subcategoria_id": servicio.subcategoria_id,
                "subcategoria_code": servicio.subcategoria.code if servicio.subcategoria else "",
                "costo_taller": str(precio_taller),
                "precio_taller": str(precio_taller),
                "precio": str(precio_cliente),
                "precio_cliente": str(precio_cliente),
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
    return render(request, "taller/common/servicios/servicios_menu.html", context)


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

    return render(request, "taller/common/servicios/servicios_menu.html", context)


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

    return render(request, "taller/common/servicios/servicios_menu.html", context)


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
