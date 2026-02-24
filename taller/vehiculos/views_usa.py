# Views específicas para USA - usan templates localizados
import logging

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.template import TemplateDoesNotExist
from django.template.loader import get_template

from taller.models.clientes import Cliente
from taller.models.vehiculos import Vehiculo
from taller.vehiculos.forms import VehiculoForm

log = logging.getLogger(__name__)


@login_required
def lista_vehiculos(request):
    """Lista vehículos para USA."""
    empresa = getattr(request.user, "empresa", None)
    if not empresa:
        messages.error(request, "User has no assigned company")
        return redirect("/")

    vehiculos = (
        Vehiculo.objects.filter(empresa=empresa)
        .select_related("cliente", "marca", "modelo", "motor", "caja", "color")
        .order_by("-id")
    )

    return render(request, "taller/us/en/vehiculos/lista_vehiculos.html", {"vehiculos": vehiculos})


@login_required
def crear_vehiculo(request, lang=None, *args, **kwargs):
    """Crear vehículo para USA."""
    empresa = getattr(request.user, "empresa", None)

    if not empresa:
        messages.error(request, "User has no assigned company")
        return redirect("/")

    # Detectar idioma desde la URL
    path = request.path.lower()
    # También verificar request.get_full_path() por si hay query params
    full_path = request.get_full_path().lower()

    log.info(f"[crear_vehiculo] Request path: {request.path}, lower: {path}")
    log.info(f"[crear_vehiculo] Full path: {request.get_full_path()}, lower: {full_path}")

    # Detectar idioma: verificar tanto en path como en full_path
    if (
        "/es/" in path
        or "/es/" in full_path
        or path.startswith("/us/es/")
        or full_path.startswith("/us/es/")
    ):
        lang = "es"
        template = "us/es/vehiculos/crear_vehiculo.html"
        error_msg = "Por favor corrige los errores en el formulario"
        create_error_msg = "Error al crear el vehículo"
        log.info(f"[crear_vehiculo] ✅ Idioma detectado: ES, template: {template}")
    else:
        lang = "en"
        template = "us/en/vehiculos/crear_vehiculo.html"
        error_msg = "Please correct the errors in the form"
        create_error_msg = "Error creating vehicle"
        log.info(f"[crear_vehiculo] ✅ Idioma detectado: EN, template: {template}")

    log.info(f"[crear_vehiculo] Template final seleccionado: {template}")

    if request.method == "POST":
        form = VehiculoForm(request.POST, user=request.user, request=request)

        if form.is_valid():
            try:
                with transaction.atomic():
                    vehiculo = form.save(commit=False)
                    vehiculo.empresa = empresa
                    vehiculo.save()

                    # Mensaje de éxito según idioma
                    if lang == "es":
                        success_msg = (
                            f"Vehículo {vehiculo.patente or 'sin patente'} creado exitosamente"
                        )
                    else:
                        success_msg = (
                            f"Vehicle {vehiculo.patente or 'without plate'} created successfully"
                        )

                    messages.success(request, success_msg)
                    return redirect("vehiculos_usa:lista_vehiculos")
            except Exception as e:
                log.error(f"Error creating vehicle: {e}")
                messages.error(request, f"{create_error_msg}: {str(e)}")
        else:
            messages.error(request, error_msg)
    else:
        form = VehiculoForm(user=request.user, request=request)

    # Obtener clientes filtrados por empresa
    clientes = Cliente.objects.filter(empresa=empresa)[:500]

    ctx = {
        "form": form,
        "country": "US",
        "empresa": empresa,
        "clientes": clientes,
        "lang": lang,  # Agregar lang al contexto para debug
        "template_path": template,  # Agregar template_path para debug
    }

    log.info(f"[crear_vehiculo] Renderizando template: {template} con lang: {lang}")
    log.info(f"[crear_vehiculo] Context keys: {list(ctx.keys())}")

    # Verificar que la plantilla existe antes de renderizar
    try:
        get_template(template)
        log.info(f"[crear_vehiculo] ✅ Template encontrado: {template}")
    except TemplateDoesNotExist:
        log.error(f"[crear_vehiculo] ❌ Template NO encontrado: {template}")
        # Fallback a inglés si la plantilla en español no existe
        if lang == "es":
            log.warning(f"[crear_vehiculo] ⚠️ Usando fallback a inglés")
            template = "us/en/vehiculos/crear_vehiculo.html"
            try:
                get_template(template)
                log.info(f"[crear_vehiculo] ✅ Template fallback encontrado: {template}")
            except TemplateDoesNotExist:
                log.error(f"[crear_vehiculo] ❌ Template fallback TAMPOCO existe: {template}")

    return render(request, template, ctx)


@login_required
def ver_vehiculo(request, pk):
    """Ver detalles de un vehículo (USA)."""
    empresa = getattr(request.user, "empresa", None)
    vehiculo = get_object_or_404(Vehiculo, id=pk, empresa=empresa)

    return render(request, "taller/us/en/vehiculos/detalle.html", {"vehiculo": vehiculo})


@login_required
def editar_vehiculo(request, vehiculo_id):
    """Editar un vehículo (USA)."""
    empresa = getattr(request.user, "empresa", None)
    vehiculo = get_object_or_404(Vehiculo, id=vehiculo_id, empresa=empresa)

    # Detectar idioma desde la URL
    path = request.path.lower()
    full_path = request.get_full_path().lower()

    if (
        "/es/" in path
        or "/es/" in full_path
        or path.startswith("/us/es/")
        or full_path.startswith("/us/es/")
    ):
        lang = "es"
        template = "us/es/vehiculos/crear_vehiculo.html"  # Usar el mismo template que crear
        success_msg_es = f"Vehículo {vehiculo.patente or 'sin patente'} actualizado exitosamente"
        error_msg_es = "Por favor corrige los errores en el formulario"
    else:
        lang = "en"
        template = "taller/us/en/vehiculos/editar_vehiculo.html"
        success_msg_es = f"Vehicle {vehiculo.patente or 'without plate'} updated successfully"
        error_msg_es = "Please correct the errors in the form"

    if request.method == "POST":
        form = VehiculoForm(request.POST, instance=vehiculo, user=request.user, request=request)

        if form.is_valid():
            try:
                with transaction.atomic():
                    form.save()
                    messages.success(request, success_msg_es)
                    return redirect("vehiculos_usa:lista_vehiculos")
            except Exception as e:
                log.error(f"Error updating vehicle: {e}")
                messages.error(request, f"Error updating vehicle: {str(e)}")
        else:
            messages.error(request, error_msg_es)
    else:
        form = VehiculoForm(instance=vehiculo, user=request.user, request=request)

    # Si es español, usar el template de crear (que tiene el formulario completo)
    # Si es inglés, usar el template específico de editar
    if lang == "es":
        # Obtener clientes filtrados por empresa para el template
        clientes = Cliente.objects.filter(empresa=empresa)[:500]
        return render(
            request,
            template,
            {
                "form": form,
                "vehiculo": vehiculo,
                "country": "US",
                "empresa": empresa,
                "clientes": clientes,
                "lang": lang,
            },
        )
    else:
        return render(
            request,
            template,
            {"form": form, "vehiculo": vehiculo},
        )
