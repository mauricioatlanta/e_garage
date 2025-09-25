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
from django.views.decorators.http import require_GET, require_POST

log = logging.getLogger(__name__)

# Modelos centrales
# Form
from taller.forms.vehiculo_simple import VehiculoFormSimple as VehiculoForm
from taller.models.clientes import Cliente

# Extras de vehículo (definir aquí la fuente AUTORITATIVA)
from taller.models.extras_vehiculo import CajaVehiculo, ColorVehiculo, MotorVehiculo
from taller.models.marca import Marca
from taller.models.modelo import Modelo
from taller.models.vehiculos import Vehiculo  # Modelo Vehiculo principal

# CBVs "shim"
from .views_cbv import VehiculoDetailView, VehiculoListView, VehiculoUpdateView

# Catálogo USA (opcional)
try:
    from taller.models.catalogo import CatalogoModeloAuto
except ImportError:
    CatalogoModeloAuto = None


# ---------------------------
# Utilidades
# ---------------------------
def _get_country(request, default="CL"):
    empresa = getattr(request.user, "empresa", None)
    raw = getattr(empresa, "pais", None) or getattr(request, "country", None) or default
    c = str(raw).strip().upper()
    return c if c in ("CL", "US") else default


def _safe_redirect(*candidates):
    """Intenta redirigir por nombre; cae al primero válido."""
    from django.urls import NoReverseMatch, reverse

    for name in candidates:
        try:
            return redirect(name)
        except NoReverseMatch:
            continue
    # Fallback muy conservador
    try:
        return redirect(reverse("taller:vehiculos:lista_vehiculos"))
    except Exception:
        return redirect("/")  # último recurso


def _render_form_with_context(request, form, country, empresa):
    """Contexto limpio para crear vehículo."""
    from django.urls import reverse
    from django.urls.exceptions import NoReverseMatch

    # Intentar diferentes namespaces según el contexto
    namespace_candidates = [
        "chile:taller:vehiculos:ajax_motores_por_modelo",
        "usa:taller:vehiculos:ajax_motores_por_modelo",
        "taller:vehiculos:ajax_motores_por_modelo",
        "vehiculos:ajax_motores_por_modelo",
    ]

    url_api_motores = None
    url_api_cajas = None

    for candidate in namespace_candidates:
        try:
            url_api_motores = reverse(candidate)
            url_api_cajas = reverse(candidate.replace("motores", "cajas"))
            break
        except NoReverseMatch:
            continue

    # Fallback a URLs relativas si no se encuentra namespace
    if not url_api_motores:
        url_api_motores = "/cl/es/vehiculos/ajax/motores-por-modelo/"
        url_api_cajas = "/cl/es/vehiculos/ajax/cajas-por-modelo/"

    ctx = {
        "country": country,
        "form": form,
        "clientes": Cliente.objects.filter(empresa=empresa)[:500],
        "colores": ColorVehiculo.objects.all().order_by("nombre"),
        "marcas": Marca.objects.filter(country=country).order_by("nombre"),
        "url_api_motores": url_api_motores,
        "url_api_cajas": url_api_cajas,
    }
    return render(request, "taller/cl/es/vehiculos/crear.html", ctx)


# ---------------------------
# API / AJAX
# ---------------------------
@require_GET
def api_marcas(request):
    """Marcas por país del usuario. Requiere auth."""
    if not request.user.is_authenticated:
        return JsonResponse([], safe=False)
    country = _get_country(request)
    data = list(
        Marca.objects.filter(country=country).order_by("nombre").values("id", "nombre")
    )
    return JsonResponse(data, safe=False)


@require_GET
@login_required
def api_busqueda_clientes(request):
    """Busca clientes solo de la empresa del usuario."""
    empresa = getattr(request.user, "empresa", None)
    if not empresa:
        return JsonResponse([], safe=False)
    q = (request.GET.get("q") or "").strip()
    if not q:
        return JsonResponse([], safe=False)
    clientes = Cliente.objects.filter(empresa=empresa).filter(
        models.Q(nombre__icontains=q)
        | models.Q(apellido__icontains=q)
        | models.Q(email__icontains=q)
        | models.Q(telefono__icontains=q)
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


@require_GET
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
def ajax_modelos_por_marca_anio(request):
    """Modelos por marca+yAÑO (si Modelo tiene 'anio' exacto)."""
    marca_id = request.GET.get("marca_id") or request.GET.get("marca")
    anio = request.GET.get("anio")

    if not marca_id:
        return JsonResponse({"results": []})

    country = _get_country(request)
    qs = Modelo.objects.filter(country=country, marca_id=marca_id)

    # Si el modelo tiene campo año, filtrar por año
    # Nota: Modelo no tiene campo año directo, pero podrías agregarlo si necesitas
    # if anio:
    #     try:
    #         anio_i = int(anio)
    #         qs = qs.filter(anio=anio_i)
    #     except ValueError:
    #         qs = qs.none()

    data = [{"id": m.pk, "text": str(m)} for m in qs.order_by("nombre")]
    return JsonResponse({"results": data})


@require_GET
@login_required
def api_modelos_usa(request):
    """Modelos USA por marca (vía catálogo opcional)."""
    marca = (request.GET.get("marca") or "").strip()
    if not marca:
        return JsonResponse({"results": []})
    try:
        if CatalogoModeloAuto:
            modelos = CatalogoModeloAuto.get_modelos_por_marca(marca)
            results = [{"id": modelo, "text": modelo} for modelo in modelos]
        else:
            results = []
        return JsonResponse({"results": results})
    except Exception as e:
        log.error(f"Error en api_modelos_usa: {e}")
        return JsonResponse({"results": [], "error": str(e)})


@login_required
def api_colores(request):
    """Colores con soporte GET (buscar) y POST (crear)."""
    if request.method == "GET":
        # Buscar colores existentes
        q = (request.GET.get("q") or "").strip()
        qs = ColorVehiculo.objects.all()
        if q:
            qs = qs.filter(nombre__icontains=q)
        data = [{"id": c.id, "text": c.nombre} for c in qs.order_by("nombre")[:50]]
        return JsonResponse({"results": data})

    elif request.method == "POST":
        # Crear nuevo color
        try:
            payload = json.loads(request.body or "{}")
            nombre = (payload.get("nombre") or "").strip()
            if not nombre:
                return JsonResponse(
                    {"success": False, "error": "Nombre requerido"}, status=400
                )

            color, created = ColorVehiculo.objects.get_or_create(
                nombre__iexact=nombre, defaults={"nombre": nombre}
            )
            return JsonResponse(
                {"success": True, "color": {"id": color.id, "nombre": color.nombre}}
            )
        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)}, status=500)

    return JsonResponse({"error": "Método no permitido"}, status=405)


# ---- Motores / Cajas por modelo (regla importante: sin modelo => lista vacía)
@require_GET
@login_required
def ajax_motores_por_modelo(request):
    modelo_id = request.GET.get("modelo_id") or request.GET.get("modelo")
    if not (modelo_id and modelo_id.isdigit()):
        return JsonResponse({"results": []})

    empresa = getattr(request.user, "empresa", None)
    if not empresa:
        return JsonResponse({"results": []})

    # Filtrar motores por modelo usando M2M + país para evitar contaminación
    qs = (
        MotorVehiculo.objects.filter(
            modelos__id=modelo_id, modelos__marca__country=empresa.pais
        )
        .distinct()
        .order_by("nombre")
        .values("id", "nombre")
    )
    return JsonResponse({"results": [{"id": r["id"], "text": r["nombre"]} for r in qs]})


@require_GET
@login_required
def ajax_cajas_por_modelo(request):
    modelo_id = request.GET.get("modelo_id") or request.GET.get("modelo")
    if not (modelo_id and modelo_id.isdigit()):
        return JsonResponse({"results": []})

    empresa = getattr(request.user, "empresa", None)
    if not empresa:
        return JsonResponse({"results": []})

    # Filtrar cajas por modelo usando M2M + país para evitar contaminación
    qs = (
        CajaVehiculo.objects.filter(
            modelos__id=modelo_id, modelos__marca__country=empresa.pais
        )
        .distinct()
        .order_by("nombre")
        .values("id", "nombre")
    )
    return JsonResponse({"results": [{"id": r["id"], "text": r["nombre"]} for r in qs]})


# ---- Crear nuevas entidades (AJAX JSON)
@require_POST
@login_required
def ajax_agregar_marca(request):
    data = json.loads(request.body or "{}")
    nombre = (data.get("nombre") or "").strip()
    country = _get_country(request)
    if not nombre:
        return JsonResponse(
            {"success": False, "error": "El nombre de la marca es requerido"}
        )
    if Marca.objects.filter(nombre__iexact=nombre, country=country).exists():
        return JsonResponse(
            {"success": False, "error": f"La marca '{nombre}' ya existe"}
        )
    nueva = Marca.objects.create(nombre=nombre, country=country)
    return JsonResponse(
        {"success": True, "marca": {"id": nueva.id, "nombre": nueva.nombre}}
    )


@require_POST
@login_required
def ajax_agregar_modelo(request):
    data = json.loads(request.body or "{}")
    nombre = (data.get("nombre") or "").strip()
    marca_id = data.get("marca_id")
    country = _get_country(request)
    if not nombre:
        return JsonResponse(
            {"success": False, "error": "El nombre del modelo es requerido"}
        )
    if not marca_id:
        return JsonResponse({"success": False, "error": "La marca es requerida"})
    try:
        marca = Marca.objects.get(id=marca_id, country=country)
    except Marca.DoesNotExist:
        return JsonResponse({"success": False, "error": "Marca no encontrada"})
    if Modelo.objects.filter(
        nombre__iexact=nombre, marca=marca, country=country
    ).exists():
        return JsonResponse(
            {
                "success": False,
                "error": f"El modelo '{nombre}' ya existe para '{marca.nombre}'",
            }
        )
    nuevo = Modelo.objects.create(nombre=nombre, marca=marca, country=country)
    return JsonResponse(
        {"success": True, "modelo": {"id": nuevo.id, "nombre": nuevo.nombre}}
    )


@require_POST
@login_required
def ajax_agregar_motor(request):
    data = json.loads(request.body or "{}")
    nombre = (data.get("nombre") or "").strip()
    modelo_id = data.get("modelo_id")

    if not nombre:
        return JsonResponse(
            {"success": False, "error": "El nombre del motor es requerido"}
        )
    if not (modelo_id and str(modelo_id).isdigit()):
        return JsonResponse({"success": False, "error": "El modelo es requerido"})

    empresa = getattr(request.user, "empresa", None)
    if not empresa:
        return JsonResponse({"success": False, "error": "Empresa no encontrada"})

    try:
        modelo = Modelo.objects.get(id=modelo_id)
    except Modelo.DoesNotExist:
        return JsonResponse({"success": False, "error": "Modelo no encontrado"})

    # Verificar si el motor ya existe para este modelo específico
    if MotorVehiculo.objects.filter(
        nombre__iexact=nombre, modelos__id=modelo_id
    ).exists():
        return JsonResponse(
            {
                "success": False,
                "error": f"El motor '{nombre}' ya existe para este modelo",
            }
        )

    # Buscar motor existente o crear uno nuevo
    motor, created = MotorVehiculo.objects.get_or_create(
        nombre__iexact=nombre, defaults={"nombre": nombre}
    )
    motor.modelos.add(modelo)
    return JsonResponse(
        {"success": True, "motor": {"id": motor.id, "nombre": motor.nombre}}
    )


@require_POST
@login_required
def ajax_agregar_caja(request):
    data = json.loads(request.body or "{}")
    nombre = (data.get("nombre") or "").strip()
    modelo_id = data.get("modelo_id")

    if not nombre:
        return JsonResponse(
            {"success": False, "error": "El nombre de la caja es requerido"}
        )
    if not (modelo_id and str(modelo_id).isdigit()):
        return JsonResponse({"success": False, "error": "El modelo es requerido"})

    empresa = getattr(request.user, "empresa", None)
    if not empresa:
        return JsonResponse({"success": False, "error": "Empresa no encontrada"})

    try:
        modelo = Modelo.objects.get(id=modelo_id)
    except Modelo.DoesNotExist:
        return JsonResponse({"success": False, "error": "Modelo no encontrado"})

    # Verificar si la caja ya existe para este modelo específico
    if CajaVehiculo.objects.filter(
        nombre__iexact=nombre, modelos__id=modelo_id
    ).exists():
        return JsonResponse(
            {
                "success": False,
                "error": f"La caja '{nombre}' ya existe para este modelo",
            }
        )

    # Buscar caja existente o crear una nueva
    caja, created = CajaVehiculo.objects.get_or_create(
        nombre__iexact=nombre, defaults={"nombre": nombre}
    )
    caja.modelos.add(modelo)
    return JsonResponse(
        {"success": True, "caja": {"id": caja.id, "nombre": caja.nombre}}
    )


# ---------------------------
# FBVs básicas (shim a CBVs)
# ---------------------------
def lista_vehiculos(request, *args, **kwargs):
    log.info("FBV shim: lista_vehiculos")
    return VehiculoListView.as_view()(request, *args, **kwargs)


def ver_vehiculo(request, *args, **kwargs):
    log.info("FBV shim: ver_vehiculo")
    return VehiculoDetailView.as_view()(request, *args, **kwargs)


def editar_vehiculo(request, *args, **kwargs):
    log.info("FBV shim: editar_vehiculo")
    vehiculo_id = kwargs.pop("vehiculo_id", None)
    if vehiculo_id is not None:
        kwargs["pk"] = vehiculo_id
    return VehiculoUpdateView.as_view()(request, *args, **kwargs)


@login_required
def crear_vehiculo(request):
    """Crear vehículo con reglas CL/US y multi-tenant."""
    empresa = getattr(request.user, "empresa", None)
    country = _get_country(request)

    if request.method == "POST":
        # Validaciones mínimas + persistencia
        form = VehiculoForm(request.POST, user=request.user, empresa=empresa)
        if not request.POST.get("cliente"):
            messages.error(request, "Debe seleccionar un cliente")
            return _render_form_with_context(request, form, country, empresa)
        if not request.POST.get("marca"):
            messages.error(request, "Debe seleccionar una marca")
            return _render_form_with_context(request, form, country, empresa)
        if not request.POST.get("modelo"):
            messages.error(request, "Debe seleccionar un modelo")
            return _render_form_with_context(request, form, country, empresa)
        if not request.POST.get("color"):
            messages.error(request, "Debe seleccionar un color")
            return _render_form_with_context(request, form, country, empresa)
        if not (request.POST.get("patente") or "").strip():
            messages.error(request, "Debe especificar la patente")
            return _render_form_with_context(request, form, country, empresa)
        if not request.POST.get("anio"):
            messages.error(request, "Debe seleccionar el año")
            return _render_form_with_context(request, form, country, empresa)

        # Construcción manual para mantener tu lógica actual
        try:
            with transaction.atomic():
                # Verificar si ya existe un vehículo con esta patente en la empresa
                patente = (request.POST.get("patente") or "").strip()
                if Vehiculo.objects.filter(empresa=empresa, patente=patente).exists():
                    messages.error(
                        request,
                        f"Ya existe un vehículo con la patente {patente} en esta empresa",
                    )
                    return _render_form_with_context(request, form, country, empresa)

                v = Vehiculo()
                # Cliente (scoped por empresa)
                v.cliente = Cliente.objects.get(
                    id=request.POST["cliente"], empresa=empresa
                )
                # Marca/Modelo por country
                v.marca = Marca.objects.get(id=request.POST["marca"], country=country)
                v.modelo = Modelo.objects.get(
                    id=request.POST["modelo"], marca=v.marca, country=country
                )

                # Color (nuevo o existente)
                color_id = request.POST.get("color")
                if color_id == "__nuevo__":
                    color_nuevo = (request.POST.get("color_nuevo") or "").strip()
                    if not color_nuevo:
                        messages.error(
                            request, "Debe especificar el nombre del nuevo color"
                        )
                        return _render_form_with_context(
                            request, form, country, empresa
                        )
                    v.color, _ = ColorVehiculo.objects.get_or_create(nombre=color_nuevo)
                else:
                    v.color = ColorVehiculo.objects.get(id=color_id)

                v.patente = patente
                v.anio = int(request.POST["anio"])
                v.vin = (request.POST.get("vin") or "").strip()

                # Opcionales (relaciones M2M viven en Motor/Caja, aquí FK opcional)
                motor_id = request.POST.get("motor")
                if motor_id:
                    v.motor = MotorVehiculo.objects.get(id=motor_id)
                caja_id = request.POST.get("caja")
                if caja_id:
                    v.caja = CajaVehiculo.objects.get(id=caja_id)

                v.empresa = empresa
                v.save()
                messages.success(request, f"Vehículo {v.patente} creado exitosamente")

                # Namespaces robustos
                return _safe_redirect(
                    "chile:taller:vehiculos:lista_vehiculos",
                    "usa:taller:vehiculos:lista_vehiculos",
                    "taller:vehiculos:lista_vehiculos",
                )
        except Exception as e:
            log.error(f"[crear_vehiculo] Error: {e}", exc_info=True)
            messages.error(request, f"Error al crear el vehículo: {str(e)}")
            return _render_form_with_context(request, form, country, empresa)
    else:
        form = VehiculoForm(user=request.user, empresa=empresa)
        return _render_form_with_context(request, form, country, empresa)


@login_required
def eliminar_vehiculo(request, vehiculo_id, *args, **kwargs):
    v = get_object_or_404(Vehiculo, pk=vehiculo_id)
    if request.method == "POST":
        v.delete()
        messages.success(request, f"Vehículo {v.patente} eliminado correctamente.")
        return _safe_redirect(
            "chile:taller:vehiculos:lista_vehiculos",
            "usa:taller:vehiculos:lista_vehiculos",
            "taller:vehiculos:lista_vehiculos",
        )
    return render(request, "taller/vehiculos/eliminar_confirmar.html", {"object": v})
