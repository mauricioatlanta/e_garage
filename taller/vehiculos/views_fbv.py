from taller.vehiculos.motor_helper import resolver_o_crear_modelo

def _resolver_modelo_flexible(modelo_id, marca_id=None, country="US"):
    """Resuelve o crea un objeto Modelo compatible tanto para catálogo USA como estándar."""
    from taller.models import Modelo, Marca
    try:
        from taller.models import ModeloVehiculo
    except ImportError:
        ModeloVehiculo = None

    modelo = None
    # 1. Intentar por ID entero directo en Modelo
    if str(modelo_id).isdigit():
        modelo = Modelo.objects.filter(id=int(modelo_id)).first()

    # 2. Intentar buscar por ModeloVehiculo (catálogo USA)
    if not modelo and ModeloVehiculo and str(modelo_id).isdigit():
        mv = ModeloVehiculo.objects.filter(id=int(modelo_id)).first()
        if mv:
            marca_obj = Marca.objects.filter(nombre__iexact=mv.marca.nombre).first()
            if not marca_obj and marca_id:
                marca_obj = Marca.objects.filter(id=marca_id).first() if str(marca_id).isdigit() else Marca.objects.filter(nombre__iexact=str(marca_id)).first()
            if marca_obj:
                modelo = Modelo.objects.filter(marca=marca_obj, nombre__iexact=mv.nombre).first()
                if not modelo:
                    modelo = Modelo.objects.create(marca=marca_obj, nombre=mv.nombre, country=country, activo=True)

    # 3. Intentar por nombre exacto/coincidente
    if not modelo and modelo_id:
        nombre_str = str(modelo_id).strip()
        qs = Modelo.objects.filter(nombre__iexact=nombre_str)
        if country:
            qs_c = qs.filter(country=country)
            if qs_c.exists():
                qs = qs_c
        modelo = qs.first()

        # Si aún no existe y tenemos la marca, crearlo automáticamente
        if not modelo and marca_id:
            marca_obj = Marca.objects.filter(id=int(marca_id)).first() if str(marca_id).isdigit() else Marca.objects.filter(nombre__iexact=str(marca_id).strip()).first()
            if marca_obj:
                modelo = Modelo.objects.create(marca=marca_obj, nombre=nombre_str, country=country, activo=True)

    return modelo

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
from urllib.parse import urlencode, urlparse, parse_qsl, urlunparse

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import models, transaction
from django.db.models.deletion import ProtectedError
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import select_template
from django.template.response import TemplateResponse
from django.urls import NoReverseMatch, reverse
from django.utils.translation import get_language
from django.views.decorators.http import require_GET, require_POST

from taller.config.country_settings import CountrySettings

log = logging.getLogger(__name__)

# Modelos centrales
# Form
from taller.models.clientes import Cliente

# Extras de vehículo (definir aquí la fuente AUTORITATIVA)
from taller.models.extras_vehiculo import (
    CajaVehiculo,
    CajaVehiculoEmpresa,
    ColorVehiculo,
    MotorVehiculo,
    MotorVehiculoEmpresa,
)
from taller.models.marca import Marca
from taller.models.modelo import Modelo
from taller.models.vehiculos import Vehiculo  # Modelo Vehiculo principal
from taller.models.vehiculo_imagen import VehiculoImagen
from taller.models.vehiculo_imagen import VehiculoImagen
from taller.common.mixins.context_return import (
    build_context_return_url,
    get_safe_context_return_url,
)
from taller.vehiculos.catalog_bootstrap import ensure_vehicle_catalog_for_country
from taller.vehiculos.forms import VehiculoForm
from taller.vehiculos.usa_model_catalog import USA_MODELS_BY_MAKE
from taller.services.empresa_service import get_empresa_safe

# CBVs "shim"
# from .views_cbv import VehiculoDetailView, VehiculoListView, VehiculoUpdateView  # No utilizados

# Catálogo USA (opcional)
try:
    from taller.models.catalogo import CatalogoModeloAuto
except ImportError:
    CatalogoModeloAuto = None

try:
    from taller.models.marcas_usa import ModeloVehiculo
except ImportError:
    ModeloVehiculo = None

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
        # US con idioma explícito: es → template con botones agregar marca/modelo
        "US_es": "us/es/vehiculos/crear_vehiculo.html",
        "US_en": "us/en/vehiculos/crear_vehiculo.html",
    },
}

DEFAULT_VEHICLE_TEMPLATES = {
    "crear": "us/en/vehiculos/crear_vehiculo.html",
}


# ---------------------------
# Utilidades
# ---------------------------
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
    """Resolve the catalog country from the route before tenant fallbacks."""
    path = (getattr(request, "path_info", None) or getattr(request, "path", "") or "").lower()
    for country, settings in CountrySettings.COUNTRIES.items():
        prefix = settings["url_prefix"].rstrip("/").lower()
        if path == prefix or path.startswith(f"{prefix}/"):
            return country

    user = getattr(request, "user", None)
    if user and getattr(user, "is_superuser", False):
        session = getattr(request, "session", {})
        support_country = (
            session.get("modo_soporte_pais")
            or session.get("support_country")
            or ""
        ).strip().upper()
        if support_country in CountrySettings.COUNTRIES:
            return support_country

    # Fall back to the active tenant when no country route/context is available.
    empresa = get_empresa_safe(request)
    raw = getattr(empresa, "pais", None)

    if not raw:
        raw = getattr(request, "country", None)

    c = str(raw or default).strip().upper()
    if c in ("US", "USA"):
        return "US"
    if c in ("MX", "MEX"):
        return "MX"
    return "CL"


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


def _append_query_params(url, **params):
    """Append or overwrite query params on a URL safely. Skips None and empty string."""
    if not url or not url.strip():
        return url
    parsed = urlparse(url)
    current = dict(parse_qsl(parsed.query, keep_blank_values=True))
    for k, v in params.items():
        if v is not None and v != "":
            current[k] = str(v)
    new_query = urlencode(current)
    return urlunparse(parsed._replace(query=new_query))


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
def _get_empresa_safe(user):
    """Obtiene la empresa del usuario sin lanzar DoesNotExist (OneToOne reverse)."""
    if not user or not getattr(user, "is_authenticated", False):
        return None
    try:
        return user.empresa
    except Exception:
        return None


@login_required
def lista_vehiculos(request):
    """Lista vehículos de la empresa del usuario para flujo taller/cliente."""
    compat_redirect = _compat_canonical_redirect(request, "vehiculos:lista_vehiculos")
    if compat_redirect:
        return compat_redirect

    empresa = get_empresa_safe(request)
    if not empresa:
        messages.error(request, "Usuario sin empresa asignada")
        return redirect("/")

    vehiculos = (
        Vehiculo.objects.filter(
            empresa=empresa,
            tipo_uso=Vehiculo.TIPO_USO_CLIENTE,
        )
        .select_related("cliente", "marca", "modelo", "motor", "caja", "color")
        .order_by("-id")
    )
    query = (request.GET.get("q") or "").strip()
    if query:
        for term in query.split():
            vehiculos = vehiculos.filter(
                models.Q(patente__icontains=term)
                | models.Q(vin__icontains=term)
                | models.Q(modelo__nombre__icontains=term)
                | models.Q(marca__nombre__icontains=term)
                | models.Q(cliente__nombre__icontains=term)
                | models.Q(cliente__apellido__icontains=term)
                | models.Q(cliente__email__icontains=term)
                | models.Q(cliente__telefono__icontains=term)
                | models.Q(cliente__tax_id__icontains=term)
            )

    # Detectar país e idioma desde la URL
    country, lang = _get_country_from_path(request.path)

    # Usar select_template con fallbacks (varias rutas por si el proyecto usa us/en o taller/us/en)
    template_obj = select_template(
        [
            f"{country}/{lang}/vehiculos/lista_vehiculos.html",
            f"taller/{country}/{lang}/vehiculos/lista_vehiculos.html",
            "taller/common/vehiculos/vehiculo_list.html",
        ]
    )

    return render(
        request,
        template_obj.template.name,
        {
            "vehiculos": vehiculos,
            "empresa": empresa,
            "search_query": query,
        },
    )


@login_required
def crear_vehiculo(request, *args, **kwargs):
    """Crear vehículo con reglas CL/US y multi-tenant."""
    lang = kwargs.pop("lang", None)
    # Si lang no viene en kwargs, detectar desde el path
    if not lang:
        _, lang = _get_country_from_path(request.path)
    compat_redirect = _compat_canonical_redirect(request, "vehiculos:crear_vehiculo")
    if compat_redirect:
        return compat_redirect

    empresa = get_empresa_safe(request)
    country = _get_country(request)
    cliente_id = (request.GET.get("cliente_id") or request.GET.get("cliente") or "").strip()

    if not empresa:
        messages.error(request, "Usuario sin empresa asignada")
        return redirect("/")

    if request.method == "POST":
        form = VehiculoForm(
            request.POST,
            request.FILES,
            user=request.user,
            country=country,
            empresa=empresa,
            request=request
        )
        if form.is_valid():
            try:
                with transaction.atomic():
                    vehiculo = form.save(commit=False)
                    vehiculo.empresa = empresa

                    # Asignar motor y caja resueltos desde clean
                    motor_res = form.cleaned_data.get('motor')
                    if motor_res and hasattr(motor_res, 'pk'):
                        vehiculo.motor = motor_res
                    elif motor_res is None:
                        vehiculo.motor = None

                    caja_res = form.cleaned_data.get('caja')
                    if caja_res and hasattr(caja_res, 'pk'):
                        vehiculo.caja = caja_res
                    elif caja_res is None:
                        vehiculo.caja = None

                    if not form.cleaned_data.get('marca'):
                        vehiculo.marca_id = None
                    if not form.cleaned_data.get('modelo'):
                        vehiculo.modelo_id = None

                    vehiculo.save()
                    if hasattr(form, 'save_m2m'):
                        form.save_m2m()

                    messages.success(
                        request,
                        f"Vehículo {vehiculo.patente or 'sin patente'} creado exitosamente",
                    )
                    return_to = get_safe_context_return_url(
                        request,
                        request.POST.get("return_to") or request.GET.get("return_to")
                    )
                    if return_to:
                        return redirect(return_to)
                    if country == "US" and lang in {"en", "es"}:
                        return redirect(f"us_{lang}:vehiculos:lista_vehiculos")
                    if country == "US":
                        return redirect("usa:taller:vehiculos:lista_vehiculos")
                    return redirect(f"{_country_namespace(country)}:taller:vehiculos:lista_vehiculos")
            except Exception as e:
                log.error(f"Error creando vehículo: {e}", exc_info=True)
                messages.error(request, f"Error al guardar el vehículo: {e}")
                form.add_error(
                    None,
                    "No se pudo guardar el vehículo. Revise los datos e intente nuevamente.",
                )
        else:
            messages.error(request, "Por favor corrija los errores en el formulario.")
    else:
        form = VehiculoForm(user=request.user, country=country, empresa=empresa, request=request)

    if request.method == "POST":
        cliente_id = (
            request.POST.get("cliente")
            or request.GET.get("cliente_id")
            or request.GET.get("cliente")
            or ""
        )
    next_val = request.GET.get("next") or request.POST.get("next") or ""
    return_to_val = (
        get_safe_context_return_url(
            request,
            request.GET.get("return_to")
            or request.POST.get("return_to")
            or request.GET.get("next")
            or request.POST.get("next")
            or "",
        )
        or ""
    )
    # Contexto para el template
    ctx = {
        "form": form,
        "country": country,
        "empresa": empresa,
        "patente_detectada": request.GET.get("patente", "").strip().upper() or None,
        "next": next_val,
        "return_to": return_to_val,
        "cliente_id": cliente_id or "",
    }

    # Usar key con idioma para seleccionar template correcto (US_es vs US_en)
    template_key = f"{country.upper()}_{lang}" if lang and country.upper() == "US" else country
    template_name = _vehicle_template("crear", template_key)
    # Precarga directa de motores y cajas para USA en el contexto
    try:
        from taller.models.extras_vehiculo import MotorVehiculo, CajaVehiculo
        ctx['motores_usa_list'] = list(MotorVehiculo.objects.filter(country='US').order_by('nombre'))
        ctx['cajas_usa_list'] = list(CajaVehiculo.objects.filter(country='US').order_by('nombre'))
    except Exception:
        ctx['motores_usa_list'] = []
        ctx['cajas_usa_list'] = []

    return render(request, template_name, ctx)


@login_required
def ver_vehiculo(request, vehiculo_id):
    """Ver detalles de un vehículo."""
    compat_redirect = _compat_canonical_redirect(request, "vehiculos:ver_vehiculo")
    if compat_redirect:
        return compat_redirect

    empresa = get_empresa_safe(request)
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

    imagenes = vehiculo.imagenes.all()

    return TemplateResponse(
        request,
        template_name,
        {
            "vehiculo": vehiculo,
            "imagenes": imagenes,
        },
    )


@login_required
def editar_vehiculo(request, vehiculo_id):
    """Editar un vehículo existente."""
    compat_redirect = _compat_canonical_redirect(request, "vehiculos:editar_vehiculo")
    if compat_redirect:
        return compat_redirect

    empresa = get_empresa_safe(request)
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

    empresa = get_empresa_safe(request)
    vehiculo = get_object_or_404(Vehiculo, id=vehiculo_id, empresa=empresa)

    if request.method == "POST":
        try:
            patente = vehiculo.patente or "sin patente"
            vehiculo.delete()
            messages.success(request, f"Vehículo {patente} eliminado exitosamente")
        except ProtectedError:
            # Caso específico: vehículos protegidos por piezas de desarme u otras FKs en PROTECT
            messages.error(
                request,
                "No se puede eliminar este vehículo porque tiene dependencias protegidas (por ejemplo, piezas de desarme asociadas).",
            )
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

    return render(
        request,
        "taller/common/vehiculos/confirmar_eliminacion_vehiculo.html",
        {"vehiculo": vehiculo},
    )


# ---------------------------
# API / AJAX
# ---------------------------
@require_GET
@login_required
def api_marcas(request):
    """Marcas por país del usuario."""
    country = _get_country(request)
    empresa = get_empresa_safe(request)
    ensure_vehicle_catalog_for_country(country)

    qs = Marca.objects.filter(country=country)
    # Si Marca tiene FK empresa, descomenta:
    # if hasattr(Marca, "empresa") and empresa:
    #     qs = qs.filter(empresa=empresa)

    data = list(qs.order_by("nombre").values("id", "nombre"))
    return JsonResponse(data, safe=False)


@require_GET
@login_required
def api_busqueda_clientes(request):
    """Busca clientes solo de la empresa del usuario (top 20, orden determinista)."""
    empresa = get_empresa_safe(request)
    if not empresa:
        return JsonResponse([], safe=False)
    q = (request.GET.get("q") or "").strip()
    if not q:
        return JsonResponse([], safe=False)
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


@require_GET
@login_required
def api_colores(request):
    """Colores disponibles para el país del usuario."""
    country = _get_country(request)
    empresa = get_empresa_safe(request)
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
def ajax_modelos_por_marca(request):
    """Modelos filtrados por marca (y por country del usuario)."""
    marca_id = request.GET.get("marca_id")
    if not marca_id:
        return JsonResponse([], safe=False)
    country = _get_country(request)
    modelos = (
        Modelo.objects.filter(marca_id=marca_id, country=country)
        .order_by("nombre")
        .values("id", "nombre")
    )
    return JsonResponse(list(modelos), safe=False)


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

    country = "US" if request.path.lower().startswith("/us/") else _get_country(request)
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

    modelos = list(qs.order_by("nombre")[:200])
    data = [{"id": modelo.pk, "nombre": str(modelo)} for modelo in modelos]
    nombres_incluidos = {modelo.nombre.casefold() for modelo in modelos}

    if country == "US" and ModeloVehiculo is not None:
        modelos_usa = ModeloVehiculo.objects.filter(
            marca__nombre__iexact=marca.nombre,
            activo=True,
        )
        if anio_str:
            try:
                anio = int(anio_str)
                modelos_usa = modelos_usa.filter(anio_inicio__lte=anio).filter(
                    models.Q(anio_fin__isnull=True) | models.Q(anio_fin__gte=anio)
                )
            except (ValueError, TypeError):
                log.warning("[modelos_por_marca_api] Año inválido para catálogo USA: %s", anio_str)

        for modelo in modelos_usa.order_by("nombre")[:200]:
            nombre = modelo.nombre.strip()
            if nombre and nombre.casefold() not in nombres_incluidos:
                # The form resolves this value by make/name and persists the shared Modelo.
                data.append({"id": f"nombre:{nombre}", "nombre": nombre})
                nombres_incluidos.add(nombre.casefold())

    if country == "US":
        modelos_predefinidos = next(
            (
                nombres
                for nombre_marca, nombres in USA_MODELS_BY_MAKE.items()
                if nombre_marca.casefold() == marca.nombre.strip().casefold()
            ),
            (),
        )
        for nombre in modelos_predefinidos:
            if nombre.casefold() not in nombres_incluidos:
                data.append({"id": f"nombre:{nombre}", "nombre": nombre})
                nombres_incluidos.add(nombre.casefold())

    data.sort(key=lambda item: item["nombre"].casefold())
    data = data[:200]
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


def ajax_agregar_marca(request):
    """Agregar nueva marca via AJAX."""
    try:
        data = json.loads(request.body)
        nombre = data.get("nombre", "").strip()
        if not nombre:
            return JsonResponse({"success": False, "error": "Nombre requerido"}, status=400)

        country = _get_country(request)
        empresa = get_empresa_safe(request)

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
        empresa = get_empresa_safe(request)
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
        empresa = get_empresa_safe(request)

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
        empresa = get_empresa_safe(request)
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


def ajax_agregar_color(request):
    """Agregar nuevo color via AJAX."""
    try:
        data = json.loads(request.body)
        nombre = data.get("nombre", "").strip()
        if not nombre:
            return JsonResponse({"success": False, "error": "Nombre requerido"}, status=400)

        country = _get_country(request)
        empresa = get_empresa_safe(request)

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
        empresa = get_empresa_safe(request)
        log.error(
            "Error agregando color: %s",
            e,
            extra={
                "user_id": request.user.id,
                "empresa_id": getattr(empresa, "id", None),
            },
        )
        return JsonResponse({"success": False, "error": str(e)}, status=500)


@login_required
@require_POST
def subir_imagenes_vehiculo(request, vehiculo_id):
    empresa = get_empresa_safe(request)

    vehiculo = get_object_or_404(
        Vehiculo,
        pk=vehiculo_id,
        empresa=empresa,
    )

    imagenes = request.FILES.getlist("imagenes")

    if not imagenes:
        return JsonResponse(
            {
                "success": False,
                "error": "No se recibieron imágenes",
            },
            status=400,
        )

    creadas = []

    for imagen in imagenes:
        item = VehiculoImagen.objects.create(
            empresa=empresa,
            vehiculo=vehiculo,
            imagen=imagen,
            tipo=request.POST.get("tipo", "otro"),
        )

        creadas.append(
            {
                "id": item.id,
                "url": item.imagen.url,
                "tipo": item.tipo,
            }
        )

    return JsonResponse(
        {
            "success": True,
            "imagenes": creadas,
        }
    )























def _resolve_ajax_model(data, country):
    from taller.models import Marca, Modelo

    modelo_value = str(data.get("modelo_id") or data.get("modelo") or "").strip()
    marca_value = str(data.get("marca_id") or data.get("marca") or "").strip()
    nombre_modelo = str(data.get("modelo_nombre") or "").strip()
    if not nombre_modelo and modelo_value and not modelo_value.isdigit():
        nombre_modelo = modelo_value.removeprefix("nombre:").strip()

    marca = None
    if marca_value:
        marcas = Marca.objects.filter(country=country)
        if marca_value.isdigit():
            marcas = marcas.filter(pk=int(marca_value))
        else:
            marcas = marcas.filter(nombre__iexact=marca_value)
        marca = marcas.first()

    if nombre_modelo and marca:
        modelo = Modelo.objects.filter(
            marca=marca,
            country=country,
            nombre__iexact=nombre_modelo,
        ).first()
        if modelo:
            return modelo
        return Modelo.objects.create(
            marca=marca,
            country=country,
            nombre=nombre_modelo,
        )

    if not modelo_value:
        return None

    if modelo_value.isdigit():
        modelos = Modelo.objects.filter(pk=int(modelo_value), country=country)
        if marca:
            modelos = modelos.filter(marca=marca)
        return modelos.first()

    nombre_modelo = modelo_value.removeprefix("nombre:").strip()
    modelos = Modelo.objects.filter(country=country, nombre__iexact=nombre_modelo)
    if marca:
        modelos = modelos.filter(marca=marca)
    return modelos.first()


def ajax_agregar_motor(request):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Método no permitido'}, status=405)
    import json
    try:
        data = json.loads(request.body.decode('utf-8')) if request.body else request.POST
    except Exception:
        data = request.POST

    nombre = (data.get('nombre') or '').strip()
    if not nombre:
        return JsonResponse({'success': False, 'error': 'El nombre del motor es requerido'}, status=400)

    try:
        from taller.models.extras_vehiculo import MotorVehiculo
    except ImportError:
        from taller.models import MotorVehiculo

    country = 'US' if '/us/' in request.path else 'CL'
    has_model = bool(data.get('modelo_id') or data.get('modelo') or data.get('modelo_nombre'))
    modelo = _resolve_ajax_model(data, country) if has_model else None
    if has_model and not modelo:
        return JsonResponse(
            {'success': False, 'error': 'No se pudo resolver el modelo seleccionado.'},
            status=400,
        )

    motor, created = MotorVehiculo.objects.get_or_create(nombre=nombre, country=country)
    if modelo and hasattr(motor, 'modelos'):
        motor.modelos.add(modelo)

    return JsonResponse(
        {
            'success': True,
            'id': motor.id,
            'nombre': motor.nombre,
            'motor': {'id': motor.id, 'nombre': motor.nombre},
        }
    )

def ajax_agregar_caja(request):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Método no permitido'}, status=405)
    import json
    try:
        data = json.loads(request.body.decode('utf-8')) if request.body else request.POST
    except Exception:
        data = request.POST

    nombre = (data.get('nombre') or '').strip()
    if not nombre:
        return JsonResponse({'success': False, 'error': 'El nombre de la transmisión es requerido'}, status=400)

    try:
        from taller.models.extras_vehiculo import CajaVehiculo
    except ImportError:
        try:
            from taller.models import CajaVehiculo
        except ImportError:
            from taller.models import Transmision as CajaVehiculo

    country = 'US' if '/us/' in request.path else 'CL'
    has_model = bool(data.get('modelo_id') or data.get('modelo') or data.get('modelo_nombre'))
    modelo = _resolve_ajax_model(data, country) if has_model else None
    if has_model and not modelo:
        return JsonResponse(
            {'success': False, 'error': 'No se pudo resolver el modelo seleccionado.'},
            status=400,
        )

    caja, created = CajaVehiculo.objects.get_or_create(nombre=nombre, country=country)
    if modelo and hasattr(caja, 'modelos'):
        caja.modelos.add(modelo)

    return JsonResponse(
        {
            'success': True,
            'id': caja.id,
            'nombre': caja.nombre,
            'caja': {'id': caja.id, 'nombre': caja.nombre},
        }
    )



def ajax_motores_por_modelo(request):
    modelo_val = request.GET.get('modelo_id') or request.GET.get('modelo')
    country = 'US' if '/us/' in request.path else 'CL'
    try:
        from taller.models.extras_vehiculo import MotorVehiculo
    except ImportError:
        from taller.models import MotorVehiculo
    qs = MotorVehiculo.objects.filter(country=country)

    has_model = bool(modelo_val or request.GET.get('modelo_nombre'))
    modelo = _resolve_ajax_model(request.GET, country) if has_model else None
    if modelo and hasattr(MotorVehiculo, 'modelos'):
        qs = qs.filter(modelos=modelo)
    else:
        qs = qs.none()

    data = [{'id': m.id, 'nombre': m.nombre, 'text': m.nombre} for m in qs.order_by('nombre').distinct()]
    return JsonResponse(data, safe=False)

def ajax_cajas_por_modelo(request):
    modelo_val = request.GET.get('modelo_id') or request.GET.get('modelo')
    country = 'US' if '/us/' in request.path else 'CL'
    try:
        from taller.models.extras_vehiculo import CajaVehiculo
    except ImportError:
        try:
            from taller.models import CajaVehiculo
        except ImportError:
            from taller.models import Transmision as CajaVehiculo
    qs = CajaVehiculo.objects.filter(country=country)

    has_model = bool(modelo_val or request.GET.get('modelo_nombre'))
    modelo = _resolve_ajax_model(request.GET, country) if has_model else None
    if modelo and hasattr(CajaVehiculo, 'modelos'):
        qs = qs.filter(modelos=modelo)
    else:
        qs = qs.none()

    data = [{'id': c.id, 'nombre': c.nombre, 'text': c.nombre} for c in qs.order_by('nombre').distinct()]
    return JsonResponse(data, safe=False)
