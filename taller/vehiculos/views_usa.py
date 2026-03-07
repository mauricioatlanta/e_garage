# Views específicas para USA - usan templates localizados
import logging
from urllib.parse import unquote, parse_qs, urlencode, urlparse, urlunparse

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.template import TemplateDoesNotExist
from django.template.loader import get_template
from django.utils.http import url_has_allowed_host_and_scheme

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

    prefill = (
        request.GET.get("prefill_cliente")
        or request.GET.get("cliente_id")
        or request.POST.get("prefill_cliente")
        or request.POST.get("cliente_id")
        or ""
    ).strip()
    prefill_cliente_nombre = None

    if request.method == "POST":
        prefill_cliente = (
            request.POST.get("prefill_cliente")
            or request.POST.get("cliente_id")
            or request.GET.get("prefill_cliente")
            or request.GET.get("cliente_id")
            or ""
        ).strip()
        post = request.POST.copy()
        if prefill_cliente.isdigit() and not post.get("cliente"):
            post["cliente"] = prefill_cliente
        form = VehiculoForm(post, user=request.user, request=request)

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
                    # next viene URL-encoded desde JS (encodeURIComponent). Decodificar 1 vez.
                    next_url = (
                        request.POST.get("next") or request.GET.get("next", "") or ""
                    ).strip()
                    next_url = unquote(next_url)
                    # Validación segura (misma host / relativa)
                    if next_url and url_has_allowed_host_and_scheme(
                        next_url, allowed_hosts={request.get_host()}
                    ):
                        if "documentos" in next_url:
                            parsed = urlparse(next_url)
                            params = parse_qs(parsed.query, keep_blank_values=True)
                            params["prefill_vehiculo"] = [str(vehiculo.pk)]
                            params["new_vehiculo_id"] = [str(vehiculo.pk)]  # legacy
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
                        log.info(f"[crear_vehiculo] next_url(decoded)={next_url}")
                        return redirect(next_url)
                    return redirect("vehiculos_usa:lista_vehiculos")
            except Exception as e:
                log.error(f"Error creating vehicle: {e}")
                messages.error(request, f"{create_error_msg}: {str(e)}")
        else:
            messages.error(request, error_msg)
    else:
        prefill_cliente = (
            (request.GET.get("prefill_cliente") or request.GET.get("cliente_id")) or ""
        ).strip()
        initial = {}
        if prefill_cliente.isdigit():
            cliente_obj = Cliente.objects.filter(empresa=empresa, pk=int(prefill_cliente)).first()
            if cliente_obj:
                initial["cliente"] = cliente_obj
        form = VehiculoForm(
            initial=initial,
            user=request.user,
            request=request,
        )
        # Prefill cliente nombre para label en front (Select2/DAL)
        if prefill.isdigit():
            try:
                cliente = Cliente.objects.filter(empresa=empresa, pk=int(prefill)).first()
                prefill_cliente_nombre = (
                    (
                        getattr(cliente, "nombre_completo", None)
                        or (
                            f"{(getattr(cliente, 'nombre', '') or '').strip()} {(getattr(cliente, 'apellido', '') or '').strip()}".strip()
                            if cliente
                            else ""
                        )
                        or (str(cliente) if cliente else prefill)
                    )
                    if cliente
                    else prefill
                )
            except (ValueError, TypeError):
                prefill_cliente_nombre = prefill

    # Obtener clientes filtrados por empresa
    clientes = Cliente.objects.filter(empresa=empresa)[:500]

    next_val = request.GET.get("next") or (
        request.POST.get("next") if request.method == "POST" else ""
    )
    prefill_cliente_val = prefill or None
    prefill_modelo_id = prefill_modelo_nombre = prefill_marca_val = None
    if request.method == "POST" and not form.is_valid():
        prefill_modelo_id = (request.POST.get("modelo") or "").strip()
        prefill_marca_val = (request.POST.get("marca") or "").strip()
        if prefill_modelo_id:
            prefill_modelo_nombre = prefill_modelo_id
    ctx = {
        "form": form,
        "country": "US",
        "empresa": empresa,
        "clientes": clientes,
        "lang": lang,
        "template_path": template,
        "next": next_val.strip() or None,
        "cliente_id": request.GET.get("cliente_id")
        or (request.POST.get("cliente_id") if request.method == "POST" else "").strip()
        or None,
        "prefill_cliente": prefill_cliente_val,
        "prefill_cliente_nombre": prefill_cliente_nombre
        or (request.POST.get("prefill_cliente_nombre") or "").strip()
        or None,
        "prefill_modelo_id": prefill_modelo_id,
        "prefill_modelo_nombre": prefill_modelo_nombre,
        "prefill_marca_val": prefill_marca_val,
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
