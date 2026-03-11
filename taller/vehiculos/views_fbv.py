# FBV limpias para Vehículos (crear/listar/ver + AJAX/API)
# Puntos clave:
# - SIN duplicados
# - Imports consistentes
# - Motores/Cajas NO se devuelven si no hay modelo
# - Filtrado por country consistente
# - Multi-tenant: clientes por empresa; catálogos por country
# - Redirect robusto con fallback

import json
import logging

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import models, transaction
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import select_template
from django.template.response import TemplateResponse
from django.urls import NoReverseMatch, reverse
from django.utils.translation import get_language
from django.views.decorators.http import require_GET, require_POST

log = logging.getLogger(__name__)

# Modelos centrales
# Form
from taller.models.clientes import Cliente
from taller.utils.empresa import ensure_empresa_matches_url_country

# Extras de vehículo (definir aquí la fuente AUTORITATIVA)
from taller.models.extras_vehiculo import CajaVehiculo, ColorVehiculo, MotorVehiculo
from taller.models.marca import Marca
from taller.models.modelo import Modelo
from taller.models.vehiculos import Vehiculo  # Modelo Vehiculo principal
from taller.vehiculos.forms import VehiculoForm

# CBVs "shim"
# from .views_cbv import VehiculoDetailView, VehiculoListView, VehiculoUpdateView  # No utilizados

# Catálogo USA (opcional)
try:
    from taller.models.catalogo import CatalogoModeloAuto
except ImportError:
    CatalogoModeloAuto = None

COUNTRY_NAMESPACES = {
    "CL": "chile",
    "US": "usa",
    "MX": "mexico",
    "VE": "venezuela",
    "PE": "peru",
    "BR": "brasil",
}

VEHICLE_TEMPLATES = {
    "crear": {
        "CL": "cl/es/vehiculos/crear.html",
        "US": "us/en/vehiculos/crear_vehiculo.html",
    },
}

DEFAULT_VEHICLE_TEMPLATES = {
    "crear": "taller/vehiculos/crear_vehiculo.html",
}


# ---------------------------
# Utilidades
# ---------------------------
def _country_lang_from_path(path: str) -> tuple[str, str]:
    """
    Extrae country y lang desde la URL path (ej: /cl/es/vehiculos/crear/).
    Usar para selección de template por URL, no por user/settings.
    """
    parts = [p for p in (path or "").split("/") if p]
    country = (parts[0] if len(parts) >= 1 else "cl").upper()
    lang = (parts[1] if len(parts) >= 2 and len(parts[1]) == 2 else "es").lower()
    return country, lang


def _get_country_from_path(path: str) -> tuple[str, str]:
    """
    Extrae country_code y lang_code desde la URL path.

    Returns:
        tuple: (country_code, lang_code) ej: ("cl", "es"), ("us", "en")
    """
    path_lower = path.lower()

    # Mapeo de prefijos a (country, lang)
    country_map = {
        "/cl/es/": ("cl", "es"),
        "/us/en/": ("us", "en"),
        "/us/es/": ("us", "es"),
        "/pe/es/": ("pe", "es"),
        "/co/es/": ("co", "es"),
        "/ec/es/": ("ec", "es"),
        "/ve/es/": ("ve", "es"),
        "/mx/es/": ("mx", "es"),
        "/br/es/": ("br", "es"),
    }

    # Buscar prefijo más largo primero
    for prefix, (country, lang) in sorted(country_map.items(), key=lambda x: -len(x[0])):
        if path_lower.startswith(prefix):
            return country, lang

    # Fallback: detectar país desde path
    if path_lower.startswith("/us/"):
        return "us", "en"
    elif path_lower.startswith("/cl/"):
        return "cl", "es"
    elif path_lower.startswith("/mx/"):
        return "mx", "es"
    elif path_lower.startswith("/pe/"):
        return "pe", "es"
    elif path_lower.startswith("/co/"):
        return "co", "es"
    elif path_lower.startswith("/ec/"):
        return "ec", "es"
    elif path_lower.startswith("/ve/"):
        return "ve", "es"
    elif path_lower.startswith("/br/"):
        return "br", "es"

    # Default
    return "cl", "es"


def _get_country(request, default="CL"):
    """País desde path primero (/us/ → US), luego request.country, empresa."""
    from taller.utils import get_country_from_request

    return get_country_from_request(request, default=default)


def _country_namespace(country: str) -> str:
    """Obtiene el namespace de URL según el país, normalizando códigos de país."""
    country = (country or "CL").upper()

    # Normalizar alias antiguos
    if country == "USA":
        country = "US"

    return COUNTRY_NAMESPACES.get(country, "chile")


def _vehicle_template(view_key: str, country: str) -> str:
    """Obtiene el template según la acción y el país, normalizando códigos de país."""
    country = (country or "CL").upper()

    # Normalizar alias antiguos
    if country == "USA":
        country = "US"

    per_country = VEHICLE_TEMPLATES.get(view_key, {})
    return per_country.get(country, DEFAULT_VEHICLE_TEMPLATES.get(view_key))


def has_field(model_cls, field_name: str) -> bool:
    """Verifica si un modelo tiene un campo específico de forma segura."""
    from django.core.exceptions import FieldDoesNotExist

    try:
        model_cls._meta.get_field(field_name)
        return True
    except FieldDoesNotExist:
        return False


def _safe_redirect(request, *candidates):
    """Intenta redirigir por nombre; cae al primero válido."""
    from django.urls import NoReverseMatch, reverse

    # Si tenemos request, priorizar según el país
    country = _get_country(request) if request else "CL"

    # Función auxiliar para reordenar candidatos
    def order_candidates(names):
        ordered = []
        for name in names:
            if country == "US":
                if "usa:" in name:
                    ordered.insert(0, name)
                elif "chile:" in name:
                    ordered.append(name)
                else:
                    ordered.insert(1 if ordered else 0, name)
            else:  # CL / MX (comparten layout base en español)
                if "chile:" in name:
                    ordered.insert(0, name)
                elif "usa:" in name:
                    ordered.append(name)
                else:
                    ordered.insert(1 if ordered else 0, name)
        return ordered

    # Intentar cada candidato en orden
    for name in order_candidates(candidates):
        try:
            url = reverse(name)  # ✅ FIX: reversear primero para lanzar NoReverseMatch
            return redirect(url)
        except NoReverseMatch:
            continue

    # Fallback muy conservador
    try:
        return redirect(reverse("taller:vehiculos:lista_vehiculos"))
    except Exception:
        return redirect("/")  # último recurso


def _compat_canonical_redirect(request, view_subpath: str, country: str | None = None):
    """
    Redirige rutas legacy /compat/... a la versión country-aware oficial.

    view_subpath ejemplo: "vehiculos:crear_vehiculo"
    """
    if not request.path.startswith("/compat/"):
        return None

    country = country or _get_country(request)
    ns_map = {
        "US": "usa",
        "MX": "mexico",
        "VE": "venezuela",
        "PE": "peru",
        "BR": "brasil",
        "CL": "chile",
    }
    candidates = []
    ns = ns_map.get(country)
    if ns:
        candidates.append(f"{ns}:taller:{view_subpath}")
    # Fallback a Chile por defecto
    candidates.append(f"chile:taller:{view_subpath}")
    candidates.append(f"taller:{view_subpath}")

    for name in candidates:
        try:
            return redirect(reverse(name))
        except NoReverseMatch:
            continue
    return None


# ---------------------------
# Vistas principales
# ---------------------------
@login_required
def lista_vehiculos(request):
    """Lista vehículos de la empresa del usuario."""
    compat_redirect = _compat_canonical_redirect(request, "vehiculos:lista_vehiculos")
    if compat_redirect:
        return compat_redirect

    empresa = getattr(request.user, "empresa", None)
    if not empresa:
        messages.error(request, "Usuario sin empresa asignada")
        return redirect("/")

    vehiculos = (
        Vehiculo.objects.filter(empresa=empresa)
        .select_related("cliente", "marca", "modelo", "motor", "caja", "color")
        .order_by("-id")
    )

    # Detectar país e idioma desde la URL
    country, lang = _get_country_from_path(request.path)

    # Namespace para enlaces a desarme (mapa de piezas)
    try:
        ns = request.resolver_match.namespace
        if isinstance(ns, (list, tuple)) and ns:
            prefix = ns[0]
        else:
            prefix = ns or "chile"
        desarme_map_url_name = f"{prefix}:desarme:mapa_piezas"
    except Exception:
        desarme_map_url_name = "chile:desarme:mapa_piezas"

    # Usar select_template con fallback a common
    template_obj = select_template(
        [
            f"{country}/{lang}/vehiculos/lista_vehiculos.html",
            "taller/common/vehiculos/vehiculo_list.html",
        ]
    )

    return render(
        request,
        template_obj.template.name,
        {
            "vehiculos": vehiculos,
            "empresa": empresa,
            "desarme_map_url_name": desarme_map_url_name,
        },
    )


@login_required
def crear_vehiculo(request, *args, **kwargs):
    """Crear vehículo con reglas CL/US y multi-tenant."""
    lang = kwargs.pop("lang", None)
    compat_redirect = _compat_canonical_redirect(request, "vehiculos:crear_vehiculo")
    if compat_redirect:
        return compat_redirect

    empresa = getattr(request.user, "empresa", None)
    country, lang = _country_lang_from_path(request.path)

    if not empresa:
        messages.error(request, "Usuario sin empresa asignada")
        return redirect("/")

    if request.method == "POST":
        form = VehiculoForm(request.POST, user=request.user, request=request)

        if form.is_valid():
            try:
                with transaction.atomic():
                    vehiculo = form.save(commit=False)
                    vehiculo.empresa = empresa
                    vehiculo.save()

                    messages.success(
                        request,
                        f"Vehículo {vehiculo.patente or 'sin patente'} creado exitosamente",
                    )
                    next_url = request.POST.get("next") or request.GET.get("next", "").strip()
                    if next_url and next_url.startswith("/") and "//" not in next_url:
                        # Si volvemos al documento, agregar new_vehiculo_id y prefill_cliente
                        if "documentos" in next_url:
                            from urllib.parse import parse_qs, urlencode, urlparse, urlunparse

                            parsed = urlparse(next_url)
                            params = parse_qs(parsed.query, keep_blank_values=True)
                            params["new_vehiculo_id"] = [str(vehiculo.pk)]
                            if vehiculo.cliente_id:
                                c = vehiculo.cliente
                                params["prefill_cliente"] = [str(vehiculo.cliente_id)]
                                nombre = (
                                    getattr(c, "nombre_completo", None)
                                    or f"{(getattr(c, 'nombre', '') or '').strip()} {(getattr(c, 'apellido', '') or '').strip()}".strip()
                                    or str(c)
                                )
                                params["prefill_cliente_nombre"] = [nombre]
                                params["prefill_cliente_email"] = [getattr(c, "email", "") or ""]
                                params["prefill_cliente_telefono"] = [
                                    getattr(c, "telefono", "") or ""
                                ]
                            next_url = urlunparse(
                                parsed._replace(query=urlencode(params, doseq=True))
                            )
                        return redirect(next_url)
                    return _safe_redirect(
                        request,
                        f"{country.lower()}:taller:vehiculos:lista_vehiculos",
                        "taller:vehiculos:lista_vehiculos",
                        "chile:taller:vehiculos:lista_vehiculos",
                        "usa:taller:vehiculos:lista_vehiculos",
                    )
            except Exception as e:
                log.error(f"Error creando vehículo: {e}")
                # Detectar error de VIN duplicado
                error_str = str(e).lower()
                if "unique constraint" in error_str and "vin" in error_str:
                    messages.error(
                        request,
                        "Ya existe un vehículo con este VIN en tu empresa. Por favor, verifica el VIN o edita el vehículo existente.",
                    )
                elif "unique constraint" in error_str and "patente" in error_str:
                    messages.error(
                        request,
                        "Ya existe un vehículo con esta patente en tu empresa. Por favor, verifica la patente o edita el vehículo existente.",
                    )
                else:
                    messages.error(request, f"Error al crear vehículo: {str(e)}")
        else:
            messages.error(request, "Por favor corrige los errores en el formulario")
    else:
        # Pre-llenar patente y cliente desde URL params (ej: ?patente=ABCD12&prefill_cliente=78)
        initial_data = {}
        patente_from_url = request.GET.get("patente", "").strip().upper()
        if patente_from_url:
            initial_data["patente"] = patente_from_url

        prefill_cliente = (
            request.GET.get("prefill_cliente") or request.GET.get("cliente_id") or ""
        ).strip()
        prefill_cliente_nombre = None
        if prefill_cliente.isdigit():
            cliente_obj = Cliente.objects.filter(empresa=empresa, pk=int(prefill_cliente)).first()
            if cliente_obj:
                initial_data["cliente"] = cliente_obj
                prefill_cliente_nombre = (
                    getattr(cliente_obj, "nombre_completo", None)
                    or f"{(getattr(cliente_obj, 'nombre', '') or '').strip()} {(getattr(cliente_obj, 'apellido', '') or '').strip()}".strip()
                    or str(cliente_obj)
                )
            else:
                prefill_cliente_nombre = prefill_cliente

        form = VehiculoForm(user=request.user, request=request, initial=initial_data)

    # Contexto para el template (next, cliente_id, prefill_cliente para volver al documento)
    next_val = request.GET.get("next") or (
        request.POST.get("next") if request.method == "POST" else ""
    )
    cliente_id_val = request.GET.get("cliente_id") or (
        request.POST.get("cliente_id") if request.method == "POST" else ""
    )
    prefill_val = (
        request.GET.get("prefill_cliente")
        or request.GET.get("cliente_id")
        or (
            request.POST.get("prefill_cliente") or request.POST.get("cliente_id")
            if request.method == "POST"
            else ""
        )
        or ""
    ).strip() or None
    prefill_nombre_val = None
    if request.method == "POST":
        prefill_nombre_val = (request.POST.get("prefill_cliente_nombre") or "").strip() or None
    elif prefill_val and prefill_val.isdigit() and empresa:
        c = Cliente.objects.filter(empresa=empresa, pk=int(prefill_val)).first()
        if c:
            prefill_nombre_val = (
                getattr(c, "nombre_completo", None)
                or f"{(getattr(c, 'nombre', '') or '').strip()} {(getattr(c, 'apellido', '') or '').strip()}".strip()
                or str(c)
            )
        else:
            prefill_nombre_val = prefill_val
    # En GET, usar el nombre ya resuelto en el bloque else (prefill_cliente_nombre solo existe en GET)
    if request.method != "POST" and prefill_val and prefill_nombre_val is None:
        try:
            prefill_nombre_val = prefill_cliente_nombre
        except NameError:
            prefill_nombre_val = prefill_val

    # Listado de clientes para el dropdown (Select2/API usa esto como fallback; API devuelve lista al abrir)
    clientes = (
        Cliente.objects.filter(empresa=empresa).order_by("nombre", "apellido", "id")[:500]
        if empresa
        else []
    )

    # Prefill modelo cuando form tiene errores (mantener valor seleccionado)
    prefill_modelo_id = prefill_modelo_nombre = prefill_marca_val = None
    if request.method == "POST":
        prefill_modelo_id = (request.POST.get("modelo") or "").strip()
        prefill_marca_val = (request.POST.get("marca") or "").strip()
        if prefill_modelo_id:
            prefill_modelo_nombre = prefill_modelo_id

    # Template por URL, no por user/settings: elimina "estoy en /cl/... pero me renderiza US"
    if country == "CL":
        template_name = "cl/es/vehiculos/crear.html"
    elif country == "US":
        template_name = (
            "us/en/vehiculos/crear_vehiculo.html"
            if lang == "en"
            else "us/es/vehiculos/crear_vehiculo.html"
        )
    else:
        template_name = "taller/vehiculos/crear_vehiculo.html"

    log.info(
        "[crear_vehiculo] path=%s resolved country=%s lang=%s template=%s",
        request.path,
        country,
        lang,
        template_name,
    )

    # Alinear empresa_id en sesión con país de URL (evita 403 en APIs /us/en/...)
    if country == "US":
        ensure_empresa_matches_url_country(request, "US")

    ctx = {
        "form": form,
        "country": country,
        "empresa": empresa,
        "clientes": clientes,
        "patente_detectada": request.GET.get("patente", "").strip().upper() or None,
        "next": next_val.strip() or None,
        "cliente_id": cliente_id_val.strip() or None,
        "prefill_cliente": prefill_val,
        "prefill_cliente_nombre": prefill_nombre_val,
        "prefill_modelo_id": prefill_modelo_id,
        "prefill_modelo_nombre": prefill_modelo_nombre,
        "prefill_marca_val": prefill_marca_val,
    }

    # URLs explícitas para US EN/US ES (evitar 403 y que autocomplete/marca/modelo no carguen)
    if country == "US":
        ns = "us_en" if lang == "en" else "us_es"
        try:
            ctx["url_api_clientes"] = reverse(f"{ns}:vehiculos:api_busqueda_clientes")
            ctx["url_autocomplete_cliente"] = reverse(f"{ns}:vehiculos:cliente_autocomplete")
            ctx["url_api_modelos_usa"] = reverse(f"{ns}:vehiculos:api_modelos_usa")
            ctx["url_modelos_por_marca_api"] = reverse(f"{ns}:vehiculos:modelos_por_marca_api")
            ctx["url_ajax_motores"] = reverse(f"{ns}:vehiculos:ajax_motores_por_modelo")
            ctx["url_ajax_cajas"] = reverse(f"{ns}:vehiculos:ajax_cajas_por_modelo")
            ctx["url_ajax_agregar_motor"] = reverse(f"{ns}:vehiculos:ajax_agregar_motor")
            ctx["url_ajax_agregar_caja"] = reverse(f"{ns}:vehiculos:ajax_agregar_caja")
            ctx["url_api_marcas_por_anio"] = reverse(f"{ns}:vehiculos:api_marcas_por_anio")
            ctx["url_api_modelos_por_marca_anio_usa"] = reverse(
                f"{ns}:vehiculos:api_modelos_por_marca_anio_usa"
            )
        except NoReverseMatch as e:
            log.warning("[crear_vehiculo] NoReverseMatch al construir URLs US: %s", e)
            ctx["url_api_clientes"] = ""
            ctx["url_autocomplete_cliente"] = ""
            ctx["url_api_modelos_usa"] = ""
            ctx["url_modelos_por_marca_api"] = ""
            ctx["url_ajax_motores"] = ""
            ctx["url_ajax_cajas"] = ""
            ctx["url_ajax_agregar_motor"] = ""
            ctx["url_ajax_agregar_caja"] = ""
            ctx["url_api_marcas_por_anio"] = ""
            ctx["url_api_modelos_por_marca_anio_usa"] = ""

    try:
        return render(request, template_name, ctx)
    except Exception as e:
        log.exception(
            "[crear_vehiculo] Error al renderizar template=%s path=%s: %s",
            template_name,
            request.path,
            e,
        )
        raise


@login_required
def ver_vehiculo(request, vehiculo_id):
    """Ver detalles de un vehículo."""
    compat_redirect = _compat_canonical_redirect(request, "vehiculos:ver_vehiculo")
    if compat_redirect:
        return compat_redirect

    empresa = getattr(request.user, "empresa", None)
    vehiculo = get_object_or_404(Vehiculo, id=vehiculo_id, empresa=empresa)

    # Usar template resolution en lugar de template hardcodeado
    from taller.utils.templates import select_country_lang_template

    country = _get_country(request, "CL")
    lang = get_language() or "es"

    template_name = select_country_lang_template(
        "vehiculos/vehiculo_detail.html",
        country,
        lang,
    )

    return TemplateResponse(request, template_name, {"vehiculo": vehiculo})


@login_required
def editar_vehiculo(request, vehiculo_id):
    """Editar un vehículo existente."""
    compat_redirect = _compat_canonical_redirect(request, "vehiculos:editar_vehiculo")
    if compat_redirect:
        return compat_redirect

    empresa = getattr(request.user, "empresa", None)
    vehiculo = get_object_or_404(Vehiculo, id=vehiculo_id, empresa=empresa)

    if request.method == "POST":
        form = VehiculoForm(request.POST, instance=vehiculo, user=request.user, request=request)

        if form.is_valid():
            try:
                with transaction.atomic():
                    form.save()
                    messages.success(
                        request,
                        f"Vehículo {vehiculo.patente or 'sin patente'} actualizado exitosamente",
                    )
                    return _safe_redirect(
                        request,
                        f"{_get_country(request).lower()}:taller:vehiculos:lista_vehiculos",
                        "taller:vehiculos:lista_vehiculos",
                        "chile:taller:vehiculos:lista_vehiculos",
                        "usa:taller:vehiculos:lista_vehiculos",
                    )
            except Exception as e:
                log.error(f"Error actualizando vehículo: {e}")
                messages.error(request, f"Error al actualizar vehículo: {str(e)}")
        else:
            messages.error(request, "Por favor corrige los errores en el formulario")
    else:
        form = VehiculoForm(instance=vehiculo, user=request.user, request=request)

    # Usar template resolution en lugar de template hardcodeado
    from taller.utils.templates import select_country_lang_template

    country = _get_country(request, "CL")
    lang = get_language() or "es"

    template_name = select_country_lang_template(
        "vehiculos/editar_vehiculo.html",
        country,
        lang,
    )

    return render(
        request,
        template_name,
        {"form": form, "vehiculo": vehiculo},
    )


@login_required
def eliminar_vehiculo(request, vehiculo_id):
    """Eliminar un vehículo."""
    compat_redirect = _compat_canonical_redirect(request, "vehiculos:eliminar_vehiculo")
    if compat_redirect:
        return compat_redirect

    empresa = getattr(request.user, "empresa", None)
    vehiculo = get_object_or_404(Vehiculo, id=vehiculo_id, empresa=empresa)

    if request.method == "POST":
        try:
            patente = vehiculo.patente or "sin patente"
            vehiculo.delete()
            messages.success(request, f"Vehículo {patente} eliminado exitosamente")
        except Exception as e:
            log.error(f"Error eliminando vehículo: {e}")
            messages.error(request, f"Error al eliminar vehículo: {str(e)}")

        return _safe_redirect(
            request,
            f"{_get_country(request).lower()}:taller:vehiculos:lista_vehiculos",
            "taller:vehiculos:lista_vehiculos",
            "chile:taller:vehiculos:lista_vehiculos",
            "usa:taller:vehiculos:lista_vehiculos",
        )

    return render(request, "taller/vehiculos/eliminar_vehiculo.html", {"vehiculo": vehiculo})


# ---------------------------
# API / AJAX
# ---------------------------
@require_GET
@login_required
def api_marcas(request):
    """Marcas por país del usuario."""
    country = _get_country(request)
    empresa = getattr(request.user, "empresa", None)

    qs = Marca.objects.filter(country=country)
    # Si Marca tiene FK empresa, descomenta:
    # if hasattr(Marca, "empresa") and empresa:
    #     qs = qs.filter(empresa=empresa)

    data = list(qs.order_by("nombre").values("id", "nombre"))
    return JsonResponse(data, safe=False)


@require_GET
@login_required
def api_busqueda_clientes(request):
    """Busca clientes solo de la empresa del usuario (top 20). Soporta id= para presección.
    Si q está vacío, devuelve los primeros 50 clientes para mostrar listado al abrir el dropdown."""
    empresa = getattr(request.user, "empresa", None)
    if not empresa:
        return JsonResponse([], safe=False)
    cliente_id = request.GET.get("id", "").strip()
    if cliente_id:
        # Seguridad: solo devolver el cliente si pertenece a la empresa del usuario
        try:
            c = Cliente.objects.get(pk=int(cliente_id), empresa=empresa)
            data = [
                {
                    "id": c.pk,
                    "nombre": c.nombre,
                    "apellido": c.apellido or "",
                    "email": c.email or "",
                    "telefono": c.telefono or "",
                }
            ]
            return JsonResponse(data, safe=False)
        except (Cliente.DoesNotExist, ValueError):
            return JsonResponse([], safe=False)
    q = (request.GET.get("q") or "").strip()
    if q:
        clientes = (
            Cliente.objects.filter(empresa=empresa)
            .filter(
                models.Q(nombre__icontains=q)
                | models.Q(apellido__icontains=q)
                | models.Q(email__icontains=q)
                | models.Q(telefono__icontains=q)
            )
            .order_by("nombre", "apellido", "id")[:20]
        )
    else:
        # q vacío: devolver primeros clientes para listado al abrir el dropdown
        clientes = Cliente.objects.filter(empresa=empresa).order_by("nombre", "apellido", "id")[:50]
    data = [
        {
            "id": c.pk,
            "nombre": c.nombre,
            "apellido": c.apellido or "",
            "email": c.email or "",
            "telefono": c.telefono or "",
        }
        for c in clientes
    ]
    return JsonResponse(data, safe=False)


@require_GET
@login_required
def api_colores(request):
    """Colores disponibles para el país del usuario."""
    country = _get_country(request)
    empresa = getattr(request.user, "empresa", None)
    colores = ColorVehiculo.get_colores_para_pais(country, empresa)
    data = [{"id": c.pk, "nombre": c.nombre} for c in colores]
    return JsonResponse(data, safe=False)


@require_GET
@login_required
def api_modelos_usa(request):
    """Modelos para USA desde catálogo."""
    marca_param = request.GET.get("marca", "").strip()
    if not marca_param:
        return JsonResponse([], safe=False)

    try:
        if CatalogoModeloAuto:
            modelos = list(CatalogoModeloAuto.get_modelos_por_marca(marca_param))[:100]
            data = [{"id": modelo, "nombre": modelo} for modelo in modelos]
            return JsonResponse(data, safe=False)
        else:
            return JsonResponse([], safe=False)
    except Exception as e:
        log.error(f"Error en api_modelos_usa: {e}")
        return JsonResponse([], safe=False)


@require_GET
@login_required
def api_marcas_por_anio(request):
    """
    Devuelve marcas disponibles para un año específico.
    Solo aplica para USA.
    """
    if _get_country(request) != "US":
        return JsonResponse([], safe=False)

    anio_str = request.GET.get("anio", "").strip()

    if not anio_str:
        return JsonResponse([], safe=False)

    try:
        anio = int(anio_str)
    except ValueError:
        return JsonResponse([], safe=False)

    try:
        marcas = list(CatalogoModeloAuto.get_marcas_por_anio(anio))[:200]
        data = [{"id": m, "nombre": m} for m in marcas]
        return JsonResponse(data, safe=False)

    except Exception as e:
        log.error(f"api_marcas_por_anio error: {e}")
        return JsonResponse([], safe=False)


@require_GET
@login_required
def api_modelos_por_marca_anio_usa(request):
    """
    Devuelve modelos para una marca y año específico.
    """
    if _get_country(request) != "US":
        return JsonResponse([], safe=False)

    marca = request.GET.get("marca", "").strip()
    anio_str = request.GET.get("anio", "").strip()

    if not marca or not anio_str:
        return JsonResponse([], safe=False)

    try:
        anio = int(anio_str)
    except ValueError:
        return JsonResponse([], safe=False)

    try:
        modelos = list(CatalogoModeloAuto.get_modelos_por_marca_anio(marca, anio))[:200]

        data = [{"id": m, "nombre": m} for m in modelos]
        return JsonResponse(data, safe=False)

    except Exception as e:
        log.error(f"api_modelos_por_marca_anio_usa error: {e}")
        return JsonResponse([], safe=False)


@require_GET
@login_required
def ajax_modelos_por_marca(request):
    """Modelos filtrados por marca. Acepta país del request y modelos sin country (globales); fallback sin filtro si vacío."""
    marca_id = request.GET.get("marca_id") or request.GET.get("marca")
    if not marca_id:
        return JsonResponse([], safe=False)

    try:
        marca_id = int(marca_id)
    except (TypeError, ValueError):
        return JsonResponse([], safe=False)

    country = _get_country(request)

    # Aceptar modelos del país y también modelos sin country (globales)
    qs = (
        Modelo.objects.filter(marca_id=marca_id)
        .filter(models.Q(country=country) | models.Q(country__isnull=True) | models.Q(country=""))
        .order_by("nombre")
    )

    # Fallback: si no hay resultados, mostrar todos los modelos de la marca
    if not qs.exists():
        qs = Modelo.objects.filter(marca_id=marca_id).order_by("nombre")

    data = list(qs.values("id", "nombre"))
    return JsonResponse(data, safe=False)


@require_GET
@login_required
def modelos_por_marca_api(request):
    """
    API endpoint para obtener modelos filtrados por marca_id y año (opcional).
    Formato de respuesta JSON: [{"id": 1, "nombre": "Modelo 1"}, ...]
    """
    marca_id = request.GET.get("marca_id") or request.GET.get("marca")
    anio_str = request.GET.get("anio")

    if not marca_id:
        log.warning(f"[modelos_por_marca_api] No se proporcionó marca_id")
        return JsonResponse([], safe=False)

    try:
        marca_id = int(marca_id)
    except (ValueError, TypeError):
        log.error(f"[modelos_por_marca_api] marca_id inválido: {marca_id}")
        return JsonResponse([], safe=False)

    country = _get_country(request)
    log.info(
        f"[modelos_por_marca_api] Buscando modelos para marca_id={marca_id}, country={country}, anio={anio_str}"
    )

    # Verificar que la marca existe
    try:
        marca = Marca.objects.get(pk=marca_id)
        marca_country = getattr(marca, "country", None)
        log.info(
            f"[modelos_por_marca_api] Marca encontrada: {marca.nombre} (country={marca_country})"
        )
    except Marca.DoesNotExist:
        log.warning(f"[modelos_por_marca_api] Marca con id={marca_id} no existe")
        return JsonResponse([], safe=False)

    # Estrategia de búsqueda: usar el country de la marca si está disponible,
    # de lo contrario usar el country detectado del request
    # Esto es importante porque los modelos deben tener el mismo country que su marca
    search_country = marca_country if marca_country else country

    # Si el country de la marca no coincide con el detectado, loguear advertencia
    if marca_country and marca_country != country:
        log.warning(
            f"[modelos_por_marca_api] Country mismatch: request={country}, marca={marca_country}. Usando country de la marca: {marca_country}"
        )

    # Query base: filtrar por país (de la marca) y marca
    qs = Modelo.objects.filter(country=search_country, marca_id=marca_id)

    # Log de conteo antes de filtrar por año
    total_before_anio = qs.count()
    log.info(
        f"[modelos_por_marca_api] Modelos encontrados antes de filtrar por año: {total_before_anio} (country={search_country})"
    )

    # Si no hay modelos con el country de la marca, intentar sin filtrar por country como fallback
    # (Solo para logging/información, no usamos el fallback para mantener consistencia de datos)
    if total_before_anio == 0:
        log.warning(
            f"[modelos_por_marca_api] No se encontraron modelos con country={search_country}. Verificando otros countries..."
        )
        qs_fallback = Modelo.objects.filter(marca_id=marca_id)
        total_fallback = qs_fallback.count()
        log.info(
            f"[modelos_por_marca_api] Modelos encontrados sin filtrar por country: {total_fallback}"
        )

        if total_fallback > 0:
            # Mostrar qué countries tienen modelos para esta marca
            paises_con_modelos = qs_fallback.values_list("country", flat=True).distinct()
            log.warning(
                f"[modelos_por_marca_api] ⚠️ Modelos encontrados pero con countries diferentes: {list(paises_con_modelos)}"
            )
            log.warning(
                f"[modelos_por_marca_api] 💡 Los modelos deben tener country={search_country} para aparecer. Ejecuta: python manage.py cargar_modelos_usa"
            )
            # Opcional: Usar fallback temporalmente si no hay modelos con el country correcto
            # Descomentar la siguiente línea si quieres mostrar modelos de otros countries temporalmente
            # qs = qs_fallback
        else:
            log.warning(
                f"[modelos_por_marca_api] No hay modelos para esta marca en ningún country. Ejecuta: python manage.py cargar_modelos_usa"
            )

    # Filtrar por año si se proporciona y el modelo tiene campo 'anio'
    if anio_str:
        try:
            anio = int(anio_str)
            # Si el modelo tiene campo 'anio', filtrar por él
            if has_field(Modelo, "anio"):
                qs = qs.filter(anio=anio)
                log.info(f"[modelos_por_marca_api] Filtrado por anio={anio} (campo directo)")
            # Si tiene rango (anio_desde/anio_hasta), ajustar aquí
            elif has_field(Modelo, "anio_desde") and has_field(Modelo, "anio_hasta"):
                qs = qs.filter(anio_desde__lte=anio, anio_hasta__gte=anio)
                log.info(
                    f"[modelos_por_marca_api] Filtrado por anio={anio} (rango anio_desde/anio_hasta)"
                )
        except (ValueError, TypeError):
            log.warning(f"[modelos_por_marca_api] Año inválido: {anio_str}")
            pass  # Ignorar si el año no es válido

    # Contar resultados finales
    total_final = qs.count()
    log.info(f"[modelos_por_marca_api] Total modelos después de filtros: {total_final}")

    # Si no hay modelos, verificar si hay modelos sin filtrar por país
    if total_final == 0:
        modelos_sin_country = Modelo.objects.filter(marca_id=marca_id).count()
        log.warning(
            f"[modelos_por_marca_api] No se encontraron modelos con country={search_country}. Total modelos sin filtrar por país: {modelos_sin_country}"
        )

        # Si hay modelos pero con otro país, sugerir en el log
        if modelos_sin_country > 0:
            paises_disponibles = (
                Modelo.objects.filter(marca_id=marca_id)
                .values_list("country", flat=True)
                .distinct()
            )
            log.warning(
                f"[modelos_por_marca_api] ⚠️ Países disponibles para esta marca: {list(paises_disponibles)}"
            )
            log.warning(
                f"[modelos_por_marca_api] 💡 Los modelos deben tener country={search_country} para aparecer. Considera actualizar los modelos existentes o crear nuevos."
            )

    # Formato de respuesta: lista de objetos con id y nombre
    data = [{"id": m.pk, "nombre": str(m)} for m in qs.order_by("nombre")[:200]]
    log.info(f"[modelos_por_marca_api] Retornando {len(data)} modelos")
    return JsonResponse(data, safe=False)


@require_GET
@login_required
def ajax_modelos_por_marca_anio(request):
    """Modelos por marca + (opcional) año, filtrados por country, formato Select2."""
    marca_id = request.GET.get("marca_id") or request.GET.get("marca")
    anio_str = request.GET.get("anio")

    if not marca_id:
        return JsonResponse({"results": []})

    country = _get_country(request)
    qs = Modelo.objects.filter(country=country, marca_id=marca_id)

    # Filtrar por año si se proporciona y el modelo tiene campo 'anio'
    if anio_str:
        try:
            anio = int(anio_str)
            # Si el modelo tiene campo 'anio', filtrar por él
            if has_field(Modelo, "anio"):
                qs = qs.filter(anio=anio)
            # Si tiene rango (anio_desde/anio_hasta), ajustar aquí
            elif has_field(Modelo, "anio_desde") and has_field(Modelo, "anio_hasta"):
                qs = qs.filter(anio_desde__lte=anio, anio_hasta__gte=anio)
        except (ValueError, TypeError):
            pass  # Ignorar si el año no es válido

    data = [{"id": m.pk, "text": str(m)} for m in qs.order_by("nombre")[:200]]
    return JsonResponse({"results": data})


@require_GET
@login_required
def ajax_motores_por_modelo(request):
    """Motores filtrados por modelo."""
    modelo_id = request.GET.get("modelo_id")
    if not modelo_id:
        return JsonResponse({"success": True, "motores": []})

    country = _get_country(request)
    # En US, evitar consultar tablas legacy que no existen en la BD actual.
    # El usuario puede agregar motor manualmente con /ajax/agregar-motor/
    if country == "US":
        return JsonResponse({"success": True, "motores": []})

    try:
        # CL/MX/otros: flujo normal (US devuelve vacío antes)
        try:
            modelo = Modelo.objects.get(pk=modelo_id, country=country)
            motores = (
                MotorVehiculo.objects.filter(modelos=modelo, country=country)
                .order_by("nombre")
                .values("id", "nombre")
            )
        except Modelo.DoesNotExist:
            return JsonResponse({"success": True, "motores": []})

        return JsonResponse({"success": True, "motores": list(motores)})
    except Exception as e:
        empresa = getattr(request.user, "empresa", None)
        log.error(
            "Error en ajax_motores_por_modelo: %s",
            e,
            extra={
                "user_id": request.user.id,
                "empresa_id": getattr(empresa, "id", None),
            },
        )
        return JsonResponse({"success": False, "error": str(e)}, status=500)


@require_GET
@login_required
def ajax_cajas_por_modelo(request):
    """Cajas filtradas por modelo."""
    modelo_id = request.GET.get("modelo_id")
    if not modelo_id:
        return JsonResponse({"success": True, "cajas": []})

    country = _get_country(request)
    # En US, evitar consultar tablas legacy que no existen en la BD actual.
    # El usuario puede agregar caja manualmente con /ajax/agregar-caja/
    if country == "US":
        return JsonResponse({"success": True, "cajas": []})

    try:
        # CL/MX/otros: flujo normal (US devuelve vacío antes)
        try:
            modelo = Modelo.objects.get(pk=modelo_id, country=country)
            cajas = (
                CajaVehiculo.objects.filter(modelos=modelo, country=country)
                .order_by("nombre")
                .values("id", "nombre")
            )
        except Modelo.DoesNotExist:
            return JsonResponse({"success": True, "cajas": []})

        return JsonResponse({"success": True, "cajas": list(cajas)})
    except Exception as e:
        empresa = getattr(request.user, "empresa", None)
        log.error(
            "Error en ajax_cajas_por_modelo: %s",
            e,
            extra={
                "user_id": request.user.id,
                "empresa_id": getattr(empresa, "id", None),
            },
        )
        return JsonResponse({"success": False, "error": str(e)}, status=500)


@require_POST
@login_required
def ajax_agregar_marca(request):
    """Agregar nueva marca via AJAX."""
    try:
        data = json.loads(request.body)
        nombre = data.get("nombre", "").strip()
        if not nombre:
            return JsonResponse({"success": False, "error": "Nombre requerido"}, status=400)

        country = _get_country(request)
        empresa = getattr(request.user, "empresa", None)

        # Evitar duplicados por case
        try:
            marca = Marca.objects.get(country=country, nombre__iexact=nombre)
            created = False
        except Marca.DoesNotExist:
            marca = Marca.objects.create(country=country, nombre=nombre)
            created = True

        return JsonResponse(
            {
                "success": True,
                "marca": {"id": str(marca.pk), "nombre": marca.nombre},
                "created": created,
            }
        )
    except Exception as e:
        empresa = getattr(request.user, "empresa", None)
        log.error(
            "Error agregando marca: %s",
            e,
            extra={
                "user_id": request.user.id,
                "empresa_id": getattr(empresa, "id", None),
            },
        )
        return JsonResponse({"success": False, "error": str(e)}, status=500)


@require_POST
@login_required
def ajax_agregar_modelo(request):
    """Agregar nuevo modelo via AJAX."""
    try:
        data = json.loads(request.body)
        nombre = data.get("nombre", "").strip()
        marca_id = data.get("marca_id")

        if not nombre or not marca_id:
            return JsonResponse(
                {"success": False, "error": "Nombre y marca requeridos"}, status=400
            )

        country = _get_country(request)
        empresa = getattr(request.user, "empresa", None)

        # Validar que marca pertenece al país
        marca = get_object_or_404(Marca, id=marca_id, country=country)

        # Evitar duplicados por case
        try:
            modelo = Modelo.objects.get(country=country, marca=marca, nombre__iexact=nombre)
            created = False
        except Modelo.DoesNotExist:
            modelo = Modelo.objects.create(country=country, marca=marca, nombre=nombre)
            created = True

        return JsonResponse(
            {
                "success": True,
                "modelo": {"id": str(modelo.pk), "nombre": modelo.nombre},
                "created": created,
            }
        )
    except Exception as e:
        empresa = getattr(request.user, "empresa", None)
        log.error(
            "Error agregando modelo: %s",
            e,
            extra={
                "user_id": request.user.id,
                "empresa_id": getattr(empresa, "id", None),
            },
        )
        return JsonResponse({"success": False, "error": str(e)}, status=500)


@require_POST
@login_required
def ajax_agregar_motor(request):
    """Agregar nuevo motor via AJAX."""
    try:
        data = json.loads(request.body)
        nombre = data.get("nombre", "").strip()
        modelo_id = data.get("modelo_id")

        if not nombre or not modelo_id:
            return JsonResponse(
                {"success": False, "error": "Nombre y modelo requeridos"}, status=400
            )

        country = _get_country(request)
        empresa = getattr(request.user, "empresa", None)

        # Validar que modelo pertenece al país
        modelo = get_object_or_404(Modelo, id=modelo_id, country=country)

        # Crear motor con country (y empresa si aplica)
        kwargs = {"nombre": nombre, "country": country}
        # if hasattr(MotorVehiculo, "empresa") and empresa:
        #     kwargs["empresa"] = empresa

        motor, created = MotorVehiculo.objects.get_or_create(**kwargs)
        motor.modelos.add(modelo)

        return JsonResponse(
            {
                "success": True,
                "motor": {"id": str(motor.pk), "nombre": motor.nombre},
                "created": created,
            }
        )
    except Exception as e:
        log.error(f"Error agregando motor: {e}")
        return JsonResponse({"success": False, "error": str(e)}, status=500)


@require_POST
@login_required
def ajax_agregar_caja(request):
    """Agregar nueva caja via AJAX."""
    try:
        data = json.loads(request.body)
        nombre = data.get("nombre", "").strip()
        modelo_id = data.get("modelo_id")

        if not nombre or not modelo_id:
            return JsonResponse(
                {"success": False, "error": "Nombre y modelo requeridos"}, status=400
            )

        country = _get_country(request)
        empresa = getattr(request.user, "empresa", None)

        # Validar que modelo pertenece al país
        modelo = get_object_or_404(Modelo, id=modelo_id, country=country)

        # Crear caja con country (y empresa si aplica)
        kwargs = {"nombre": nombre, "country": country}
        # if hasattr(CajaVehiculo, "empresa") and empresa:
        #     kwargs["empresa"] = empresa

        caja, created = CajaVehiculo.objects.get_or_create(**kwargs)
        caja.modelos.add(modelo)

        return JsonResponse(
            {
                "success": True,
                "caja": {"id": str(caja.pk), "nombre": caja.nombre},
                "created": created,
            }
        )
    except Exception as e:
        log.error(f"Error agregando caja: {e}")
        return JsonResponse({"success": False, "error": str(e)}, status=500)


@require_POST
@login_required
def ajax_agregar_color(request):
    """Agregar nuevo color via AJAX."""
    try:
        data = json.loads(request.body)
        nombre = data.get("nombre", "").strip()
        if not nombre:
            return JsonResponse({"success": False, "error": "Nombre requerido"}, status=400)

        country = _get_country(request)
        empresa = getattr(request.user, "empresa", None)

        # Evitar duplicados por case
        try:
            color = ColorVehiculo.objects.get(country=country, nombre__iexact=nombre)
            created = False
        except ColorVehiculo.DoesNotExist:
            color = ColorVehiculo.objects.create(country=country, nombre=nombre)
            created = True

        return JsonResponse(
            {
                "success": True,
                "color": {"id": str(color.pk), "nombre": color.nombre},
                "created": created,
            }
        )
    except Exception as e:
        empresa = getattr(request.user, "empresa", None)
        log.error(
            "Error agregando color: %s",
            e,
            extra={
                "user_id": request.user.id,
                "empresa_id": getattr(empresa, "id", None),
            },
        )
        return JsonResponse({"success": False, "error": str(e)}, status=500)
