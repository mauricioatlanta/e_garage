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
    """Detección robusta de país con fallback por path y normalización."""
    # 1) user.empresa.pais
    empresa = getattr(request.user, "empresa", None)
    raw = getattr(empresa, "pais", None)

    # 2) request.country si algún middleware/context processor lo define
    if not raw:
        raw = getattr(request, "country", None)

    # 3) Path fallback: /us/..., /cl/...
    if not raw:
        p = (request.path or "").lower()
        if p.startswith("/us/"):
            raw = "US"
        elif p.startswith("/cl/"):
            raw = "CL"
        elif p.startswith("/mx/"):
            raw = "MX"

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
    country = _get_country(request)

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
        # Pre-llenar patente desde URL params (ej: /vehiculos/crear/?patente=ABCD12)
        initial_data = {}
        patente_from_url = request.GET.get('patente', '').strip().upper()
        if patente_from_url:
            initial_data['patente'] = patente_from_url
        
        form = VehiculoForm(user=request.user, request=request, initial=initial_data)

    # Contexto para el template
    ctx = {
        "form": form,
        "country": country,
        "empresa": empresa,
        "patente_detectada": request.GET.get('patente', '').strip().upper() or None,
    }

    template_name = _vehicle_template("crear", country)
    return render(request, template_name, ctx)


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
    """Busca clientes solo de la empresa del usuario (top 20, orden determinista)."""
    empresa = getattr(request.user, "empresa", None)
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

    try:
        country = _get_country(request)

        # Para USA, buscar motores que estén asociados a modelos equivalentes
        if country == "US":
            # Buscar el modelo USA
            try:
                from taller.models.marcas_usa import ModeloVehiculo as ModeloUSA

                modelo_usa = ModeloUSA.objects.get(pk=modelo_id)

                # Buscar el modelo equivalente en el sistema Chile
                from taller.models.marca import Marca
                from taller.models.modelo import Modelo

                marca_chile = Marca.objects.filter(
                    nombre=modelo_usa.marca.nombre, country="US"
                ).first()

                if marca_chile:
                    modelo_chile = Modelo.objects.filter(
                        nombre=modelo_usa.nombre, marca=marca_chile, country="US"
                    ).first()

                    if modelo_chile:
                        motores = (
                            MotorVehiculo.objects.filter(modelos=modelo_chile, country=country)
                            .order_by("nombre")
                            .values("id", "nombre")
                        )
                    else:
                        motores = MotorVehiculo.objects.none()
                else:
                    motores = MotorVehiculo.objects.none()

            except ModeloUSA.DoesNotExist:
                return JsonResponse({"success": True, "motores": []})
        else:
            # Para Chile, usar el sistema normal
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

    try:
        country = _get_country(request)

        # Para USA, buscar cajas que estén asociadas a modelos equivalentes
        if country == "US":
            # Buscar el modelo USA
            try:
                from taller.models.marcas_usa import ModeloVehiculo as ModeloUSA

                modelo_usa = ModeloUSA.objects.get(pk=modelo_id)

                # Buscar el modelo equivalente en el sistema Chile
                from taller.models.marca import Marca
                from taller.models.modelo import Modelo

                marca_chile = Marca.objects.filter(
                    nombre=modelo_usa.marca.nombre, country="US"
                ).first()

                if marca_chile:
                    modelo_chile = Modelo.objects.filter(
                        nombre=modelo_usa.nombre, marca=marca_chile, country="US"
                    ).first()

                    if modelo_chile:
                        cajas = (
                            CajaVehiculo.objects.filter(modelos=modelo_chile, country=country)
                            .order_by("nombre")
                            .values("id", "nombre")
                        )
                    else:
                        cajas = CajaVehiculo.objects.none()
                else:
                    cajas = CajaVehiculo.objects.none()

            except ModeloUSA.DoesNotExist:
                return JsonResponse({"success": True, "cajas": []})
        else:
            # Para Chile, usar el sistema normal
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
