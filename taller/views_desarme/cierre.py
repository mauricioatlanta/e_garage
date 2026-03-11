"""
Cierre de vehículo de desarme.
"""

from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods

from taller.forms.cierre_vehiculo_desarme import CierreVehiculoDesarmeForm
from taller.models import Vehiculo
from taller.utils.empresa import get_or_create_empresa
from taller.utils.url_helpers import reverse_country


def _get_vehiculo_desarme(request, pk):
    empresa = get_or_create_empresa(request)
    return get_object_or_404(
        Vehiculo,
        pk=pk,
        empresa=empresa,
        tipo_uso="desarme",
    )


@login_required
@require_http_methods(["GET", "POST"])
def cerrar_vehiculo_desarme(request, pk):
    """Cierre lógico: fecha, peso kg, valor/kg → estado cerrado, ingreso chatarra."""
    vehiculo = _get_vehiculo_desarme(request, pk)
    if (vehiculo.estado_desarme or "").strip() == "cerrado":
        messages.warning(request, "Este vehículo ya está cerrado.")
        return redirect(
            reverse_country(request, "desarme:dashboard_financiero", kwargs={"pk": vehiculo.pk})
        )

    if request.method == "POST":
        form = CierreVehiculoDesarmeForm(request.POST)
        if form.is_valid():
            fecha = form.cleaned_data["fecha_cierre"]
            peso = form.cleaned_data["peso_final_kg"] or Decimal("0")
            valor_kg = form.cleaned_data["valor_final_por_kg"] or Decimal("0")
            obs = (form.cleaned_data.get("observaciones") or "").strip()
            vehiculo.cerrar_desarme(fecha, peso, valor_kg)
            if obs:
                vehiculo.observaciones_desarme = obs
                vehiculo.save(update_fields=["observaciones_desarme"])
            messages.success(request, "Vehículo cerrado correctamente.")
            return redirect(
                reverse_country(request, "desarme:dashboard_financiero", kwargs={"pk": vehiculo.pk})
            )
    else:
        form = CierreVehiculoDesarmeForm()

    context = {
        "vehiculo": vehiculo,
        "form": form,
    }
    return render(request, "taller/desarme/cierre_vehiculo_form.html", context)
