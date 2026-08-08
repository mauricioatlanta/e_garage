# Vistas del módulo Desarme: vehículos tipo DESARME y piezas (solo empresa, tipo_uso=DESARME)

import logging

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render

from taller.models.empresa import Empresa
from taller.models.pieza_desarme import ESTADO_VENDIDA, PiezaDesarme
from taller.models.vehiculo_desarme import VehiculoDesarme
from taller.models.vehiculos import Vehiculo

from .forms import PiezaDesarmeForm, VehiculoDesarmeForm

log = logging.getLogger(__name__)


def _empresa_or_redirect(request):
    """Obtiene la empresa del usuario o redirige con error."""
    empresa = getattr(request.user, "empresa", None)
    if not empresa:
        messages.error(request, "Usuario sin empresa asignada.")
        return None
    return empresa


@login_required
def index(request):
    """Entrada al módulo Desarme: redirige al listado de vehículos de desarme."""
    return redirect("desarme:lista_vehiculos")


@login_required
def lista_vehiculos(request):
    """Listado de vehículos de desarme con búsqueda, filtro por estado y conteo de piezas."""
    empresa = _empresa_or_redirect(request)
    if not empresa:
        return redirect("/")

    qs = (
        VehiculoDesarme.objects.filter(empresa=empresa)
        .select_related("marca", "modelo", "color")
        .annotate(piezas_count=Count("piezas_desarme"))
        .order_by("-fecha_ingreso_desarme", "-id")
    )

    q = request.GET.get("q", "").strip()
    if q:
        qs = qs.filter(
            Q(patente__icontains=q)
            | Q(vin__icontains=q)
            | Q(marca_texto__icontains=q)
            | Q(modelo_texto__icontains=q)
            | Q(marca__nombre__icontains=q)
            | Q(modelo__nombre__icontains=q)
        )

    estado = request.GET.get("estado", "").strip()
    if estado:
        qs = qs.filter(estado_desarme=estado)

    estados = (
        VehiculoDesarme.objects.filter(empresa=empresa)
        .exclude(estado_desarme__isnull=True)
        .exclude(estado_desarme="")
        .values_list("estado_desarme", flat=True)
        .distinct()
        .order_by("estado_desarme")
    )

    return render(
        request,
        "taller/desarme/lista_vehiculos.html",
        {
            "vehiculos": qs,
            "empresa": empresa,
            "q": q,
            "estado_filtro": estado,
            "estados": list(estados),
        },
    )


@login_required
def crear_vehiculo(request):
    """Alta de vehículo de desarme."""
    empresa = _empresa_or_redirect(request)
    if not empresa:
        return redirect("/")

    if request.method == "POST":
        form = VehiculoDesarmeForm(request.POST, empresa=empresa)
        if form.is_valid():
            try:
                with transaction.atomic():
                    vehiculo = form.save(commit=False)
                    vehiculo.empresa = empresa
                    vehiculo.save()
                messages.success(
                    request, f"Vehículo de desarme {vehiculo.patente or vehiculo.vin} creado."
                )
                return redirect("desarme:ver_vehiculo", pk=vehiculo.pk)
            except Exception as e:
                log.exception("Error creando vehículo de desarme")
                messages.error(request, f"Error al guardar: {e}")
        else:
            messages.error(request, "Corrija los errores del formulario.")
    else:
        form = VehiculoDesarmeForm(empresa=empresa)

    return render(
        request,
        "taller/desarme/vehiculo_form.html",
        {"form": form, "empresa": empresa, "titulo": "Nuevo vehículo de desarme"},
    )


@login_required
def ver_vehiculo(request, pk):
    """Detalle de un vehículo de desarme con resumen operativo (piezas activas/vendidas, costo)."""
    empresa = _empresa_or_redirect(request)
    if not empresa:
        return redirect("/")

    vehiculo = get_object_or_404(
        VehiculoDesarme,
        pk=pk,
        empresa=empresa,
    )
    piezas = vehiculo.piezas_desarme.filter(activo=True).order_by("codigo")
    piezas_activas_count = piezas.count()
    piezas_vendidas_count = vehiculo.piezas_desarme.filter(estado_pieza=ESTADO_VENDIDA).count()

    return render(
        request,
        "taller/desarme/ver_vehiculo.html",
        {
            "vehiculo": vehiculo,
            "piezas": piezas,
            "empresa": empresa,
            "piezas_activas_count": piezas_activas_count,
            "piezas_vendidas_count": piezas_vendidas_count,
        },
    )


@login_required
def editar_vehiculo(request, pk):
    """Edición de vehículo de desarme."""
    empresa = _empresa_or_redirect(request)
    if not empresa:
        return redirect("/")

    vehiculo = get_object_or_404(
        VehiculoDesarme,
        pk=pk,
        empresa=empresa,
    )

    if request.method == "POST":
        form = VehiculoDesarmeForm(request.POST, instance=vehiculo, empresa=empresa)
        if form.is_valid():
            try:
                form.save()
                messages.success(request, "Vehículo actualizado.")
                return redirect("desarme:ver_vehiculo", pk=vehiculo.pk)
            except Exception as e:
                log.exception("Error actualizando vehículo de desarme")
                messages.error(request, f"Error al guardar: {e}")
        else:
            messages.error(request, "Corrija los errores del formulario.")
    else:
        form = VehiculoDesarmeForm(instance=vehiculo, empresa=empresa)

    return render(
        request,
        "taller/desarme/vehiculo_form.html",
        {
            "form": form,
            "vehiculo": vehiculo,
            "empresa": empresa,
            "titulo": "Editar vehículo de desarme",
        },
    )


@login_required
def lista_piezas(request):
    """Listado de piezas con búsqueda por código/nombre y filtros por estado y vehículo."""
    empresa = _empresa_or_redirect(request)
    if not empresa:
        return redirect("/")

    piezas = (
        PiezaDesarme.objects.filter(empresa=empresa)
        .select_related("vehiculo_desarme")
        .order_by("vehiculo_desarme__patente", "codigo")
    )

    q = request.GET.get("q", "").strip()
    if q:
        piezas = piezas.filter(Q(codigo__icontains=q) | Q(nombre__icontains=q))

    estado = request.GET.get("estado", "").strip()
    if estado:
        piezas = piezas.filter(estado_pieza=estado)

    vehiculo_id = request.GET.get("vehiculo", "").strip()
    if vehiculo_id:
        piezas = piezas.filter(vehiculo_desarme_id=vehiculo_id)

    _vqs = (
        VehiculoDesarme.objects.filter(empresa=empresa)
        .select_related("marca", "modelo")
        .order_by("patente", "vin")
    )
    vehiculos_choices = []
    for v in _vqs:
        tag = v.patente or v.vin or str(v.id)
        parts = []
        if v.anio:
            parts.append(str(v.anio))
        parts.append(v.get_marca_display())
        parts.append(v.get_modelo_display())
        parts.append(tag)
        vehiculos_choices.append((v.id, " · ".join(parts)))
    from taller.models.pieza_desarme import ESTADO_PIEZA_CHOICES

    return render(
        request,
        "taller/desarme/lista_piezas.html",
        {
            "piezas": piezas,
            "empresa": empresa,
            "q": q,
            "estado_filtro": estado,
            "vehiculo_filtro": vehiculo_id,
            "vehiculos_choices": vehiculos_choices,
            "estado_pieza_choices": ESTADO_PIEZA_CHOICES,
        },
    )


@login_required
def crear_pieza(request):
    """Alta de pieza de desarme. Opcional ?vehiculo=<id> para pre-seleccionar vehículo."""
    empresa = _empresa_or_redirect(request)
    if not empresa:
        return redirect("/")

    vehiculo = None
    vehiculo_id = request.GET.get("vehiculo")
    if vehiculo_id:
        vehiculo = VehiculoDesarme.objects.filter(
            pk=vehiculo_id,
            empresa=empresa,
        ).first()

    if request.method == "POST":
        form = PiezaDesarmeForm(request.POST, empresa=empresa, vehiculo=vehiculo)
        if form.is_valid():
            try:
                with transaction.atomic():
                    pieza = form.save(commit=False)
                    pieza.empresa = empresa
                    pieza.save()
                messages.success(request, f"Pieza {pieza.codigo} creada.")
                if pieza.vehiculo_desarme_id:
                    return redirect("desarme:inventario_inteligente", pk=pieza.vehiculo_desarme_id)
                return redirect("desarme:lista_piezas")
            except Exception as e:
                log.exception("Error creando pieza de desarme")
                messages.error(request, f"Error al guardar: {e}")
        else:
            messages.error(request, "Corrija los errores del formulario.")
    else:
        form = PiezaDesarmeForm(empresa=empresa, vehiculo=vehiculo)

    return render(
        request,
        "taller/desarme/pieza_form.html",
        {
            "form": form,
            "empresa": empresa,
            "vehiculo": vehiculo,
            "titulo": "Nueva pieza de desarme",
        },
    )


@login_required
def editar_pieza(request, pk):
    """Edición de pieza de desarme."""
    empresa = _empresa_or_redirect(request)
    if not empresa:
        return redirect("/")

    pieza = get_object_or_404(PiezaDesarme, pk=pk, empresa=empresa)

    if request.method == "POST":
        form = PiezaDesarmeForm(request.POST, instance=pieza, empresa=empresa)
        if form.is_valid():
            try:
                form.save()
                messages.success(request, "Pieza actualizada.")
                if pieza.vehiculo_desarme_id:
                    return redirect("desarme:inventario_inteligente", pk=pieza.vehiculo_desarme_id)
                return redirect("desarme:lista_piezas")
            except Exception as e:
                log.exception("Error actualizando pieza de desarme")
                messages.error(request, f"Error al guardar: {e}")
        else:
            messages.error(request, "Corrija los errores del formulario.")
    else:
        form = PiezaDesarmeForm(instance=pieza, empresa=empresa)

    return render(
        request,
        "taller/desarme/pieza_form.html",
        {"form": form, "pieza": pieza, "empresa": empresa, "titulo": "Editar pieza de desarme"},
    )


