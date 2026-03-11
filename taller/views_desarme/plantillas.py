"""
Vistas para plantillas de desarme.
"""

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods

from taller.forms.plantilla_aplicar import AplicarPlantillaForm
from taller.utils.url_helpers import reverse_country
from taller.forms.plantilla_desarme import PlantillaDesarmeForm, PlantillaPiezaForm
from taller.models import PlantillaDesarme, PlantillaPieza, Vehiculo
from taller.services.plantilla_desarme_service import (
    PlantillaDesarmeError,
    aplicar_plantilla,
    plantillas_disponibles_para,
)
from taller.utils.empresa import get_or_create_empresa


def _get_empresa(request):
    return get_or_create_empresa(request)


def _plantillas_queryset(empresa):
    """Plantillas visibles: globales + propias."""
    return (
        PlantillaDesarme.objects.filter(Q(empresa__isnull=True) | Q(empresa=empresa))
        .annotate(num_piezas=Count("piezas", filter=Q(piezas__activo=True)))
        .order_by("nombre")
    )


@login_required
def plantilla_list(request):
    """Listado de plantillas de desarme."""
    empresa = _get_empresa(request)
    plantillas = _plantillas_queryset(empresa)
    context = {
        "plantillas": plantillas,
    }
    return render(request, "taller/desarme/plantillas/plantilla_list.html", context)


@login_required
def plantilla_detail(request, pk):
    """Detalle de plantilla con checklist de piezas."""
    empresa = _get_empresa(request)
    plantilla = get_object_or_404(
        PlantillaDesarme,
        pk=pk,
    )
    if plantilla.empresa_id and plantilla.empresa_id != empresa.id:
        return redirect("taller:desarme:plantilla_list")
    piezas = plantilla.piezas.filter(activo=True).order_by("orden", "id")
    context = {
        "plantilla": plantilla,
        "piezas": piezas,
        "es_global": plantilla.empresa_id is None,
    }
    return render(request, "taller/desarme/plantillas/plantilla_detail.html", context)


@login_required
@require_http_methods(["GET", "POST"])
def plantilla_create(request):
    """Crear plantilla (empresa del usuario)."""
    empresa = _get_empresa(request)
    if request.method == "POST":
        form = PlantillaDesarmeForm(request.POST, empresa=empresa)
        if form.is_valid():
            plantilla = form.save(commit=False)
            plantilla.empresa = empresa
            plantilla.save()
            messages.success(request, f"Plantilla '{plantilla.nombre}' creada.")
            return redirect("taller:desarme:plantilla_detail", pk=plantilla.pk)
    else:
        form = PlantillaDesarmeForm(empresa=empresa)
    context = {"form": form, "titulo": "Nueva plantilla"}
    return render(request, "taller/desarme/plantillas/plantilla_form.html", context)


@login_required
@require_http_methods(["GET", "POST"])
def plantilla_edit(request, pk):
    """Editar plantilla (solo propias, no globales)."""
    empresa = _get_empresa(request)
    plantilla = get_object_or_404(PlantillaDesarme, pk=pk)
    if plantilla.empresa_id is None:
        messages.warning(request, "No se pueden editar plantillas globales.")
        return redirect("taller:desarme:plantilla_detail", pk=pk)
    if plantilla.empresa_id != empresa.id:
        return redirect("taller:desarme:plantilla_list")
    if request.method == "POST":
        form = PlantillaDesarmeForm(request.POST, instance=plantilla, empresa=empresa)
        if form.is_valid():
            form.save()
            messages.success(request, f"Plantilla '{plantilla.nombre}' actualizada.")
            return redirect("taller:desarme:plantilla_detail", pk=plantilla.pk)
    else:
        form = PlantillaDesarmeForm(instance=plantilla, empresa=empresa)
    context = {"form": form, "plantilla": plantilla, "titulo": f"Editar {plantilla.nombre}"}
    return render(request, "taller/desarme/plantillas/plantilla_form.html", context)


@login_required
@require_http_methods(["GET", "POST"])
def plantilla_aplicar(request, pk):
    """Aplicar plantilla a vehículo de desarme."""
    empresa = _get_empresa(request)
    vehiculo = get_object_or_404(
        Vehiculo,
        pk=pk,
        empresa=empresa,
        tipo_uso="desarme",
    )
    if (vehiculo.estado_desarme or "").strip() == "cerrado":
        messages.error(request, "El vehículo está cerrado. No se pueden agregar piezas.")
        return redirect(
            reverse_country(request, "vehiculos:ver_vehiculo", kwargs={"vehiculo_id": vehiculo.pk})
        )

    if request.method == "POST":
        form = AplicarPlantillaForm(request.POST, empresa=empresa)
        if form.is_valid():
            plantilla = form.cleaned_data["plantilla"]
            try:
                repuestos = aplicar_plantilla(vehiculo, plantilla)
                count = len(repuestos)
                messages.success(
                    request,
                    f"Se crearon {count} piezas desde la plantilla '{plantilla.nombre}'.",
                )
                mapa_url = reverse_country(
                    request, "desarme:mapa_piezas", kwargs={"pk": vehiculo.pk}
                )
                repuestos_url = reverse_country(request, "repuestos:lista_repuestos")
                vehiculo_url = reverse_country(
                    request, "vehiculos:ver_vehiculo", kwargs={"vehiculo_id": vehiculo.pk}
                )
                request.session["desarme_apply_success"] = {
                    "count": count,
                    "mapa_url": mapa_url,
                    "repuestos_url": f"{repuestos_url}?vehiculo_origen={vehiculo.pk}",
                    "vehiculo_url": vehiculo_url,
                }
                return redirect(mapa_url)
            except PlantillaDesarmeError as e:
                messages.error(request, str(e))
    else:
        form = AplicarPlantillaForm(empresa=empresa)

    plantillas = plantillas_disponibles_para(empresa)
    for p in plantillas:
        p._num_piezas = p.piezas.filter(activo=True).count()
    context = {
        "form": form,
        "vehiculo": vehiculo,
        "plantillas": plantillas,
    }
    return render(request, "taller/desarme/plantillas/plantilla_aplicar.html", context)
