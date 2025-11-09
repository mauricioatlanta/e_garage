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


# ---------------------------
# Utilidades
# ---------------------------
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

    c = str(raw or default).strip().upper()
    return "US" if c in ("US", "USA") else "CL"


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
            else:  # CL
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


# ---------------------------
# Vistas principales
# ---------------------------
@login_required
def lista_vehiculos(request):
    """Lista vehículos de la empresa del usuario."""
    empresa = getattr(request.user, "empresa", None)
    if not empresa:
        messages.error(request, "Usuario sin empresa asignada")
        return redirect("/")

    vehiculos = (
        Vehiculo.objects.filter(empresa=empresa)
        .select_related("cliente", "marca", "modelo", "motor", "caja", "color")
        .order_by("-id")
    )

    # Usar template específico según la URL (no el país de la empresa)
    if request.path.startswith("/us/"):
        template = "taller/us/en/vehiculos/lista_vehiculos.html"
    else:
        template = "taller/vehiculos/vehiculos.html"

    return render(request, template, {"vehiculos": vehiculos})


@login_required
def crear_vehiculo(request):
    """Crear vehículo con reglas CL/US y multi-tenant."""
    empresa = getattr(request.user, "empresa", None)
    country = _get_country(request)

    if not empresa:
        messages.error(request, "Usuario sin empresa asignada")
        return redirect("/")

    if request.method == "POST":
        form = VehiculoForm(request.POST, user=request.user)

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
                messages.error(request, f"Error al crear vehículo: {str(e)}")
        else:
            messages.error(request, "Por favor corrige los errores en el formulario")
    else:
        form = VehiculoForm(user=request.user)

    # Contexto para el template
    ctx = {
        "form": form,
        "country": country,
        "empresa": empresa,
    }

    return render(request, "taller/vehiculos/crear_vehiculo.html", ctx)


@login_required
def ver_vehiculo(request, vehiculo_id):
    """Ver detalles de un vehículo."""
    empresa = getattr(request.user, "empresa", None)
    vehiculo = get_object_or_404(Vehiculo, id=vehiculo_id, empresa=empresa)

    return render(
        request, "taller/vehiculos/vehiculo_detail.html", {"vehiculo": vehiculo}
    )


@login_required
def editar_vehiculo(request, vehiculo_id):
    """Editar un vehículo existente."""
    empresa = getattr(request.user, "empresa", None)
    vehiculo = get_object_or_404(Vehiculo, id=vehiculo_id, empresa=empresa)

    if request.method == "POST":
        form = VehiculoForm(request.POST, instance=vehiculo, user=request.user)

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
        form = VehiculoForm(instance=vehiculo, user=request.user)

    return render(
        request,
        "taller/vehiculos/editar_vehiculo.html",
        {"form": form, "vehiculo": vehiculo},
    )


@login_required
def eliminar_vehiculo(request, vehiculo_id):
    """Eliminar un vehículo."""
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

    return render(
        request, "taller/vehiculos/eliminar_vehiculo.html", {"vehiculo": vehiculo}
    )


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
                            MotorVehiculo.objects.filter(
                                modelos=modelo_chile, country=country
                            )
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
                            CajaVehiculo.objects.filter(
                                modelos=modelo_chile, country=country
                            )
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
            return JsonResponse(
                {"success": False, "error": "Nombre requerido"}, status=400
            )

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
            modelo = Modelo.objects.get(
                country=country, marca=marca, nombre__iexact=nombre
            )
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
