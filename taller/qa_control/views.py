from django.contrib import messages
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST

from taller.models.configuracion import ConfiguracionEmpresa
from taller.models.empresa import Empresa

from .auth import control_tower_required
from .context import (
    clear_qa_control_context,
    find_qa_empresas,
    get_qa_control_context,
    resolve_qa_empresa,
    set_qa_control_context,
)


def _choices(field):
    return [{"value": value, "label": label} for value, label in field.choices]


def _countries():
    return _choices(Empresa._meta.get_field("pais"))


def _rubros():
    return _choices(ConfiguracionEmpresa._meta.get_field("rubro_principal"))


@control_tower_required
def control(request):
    selected = get_qa_control_context(request)
    error = None
    candidates = []
    country = (request.POST.get("country") or request.GET.get("country") or "").upper()
    rubro = (request.POST.get("rubro") or request.GET.get("rubro") or "").upper()

    if country and rubro:
        candidates = list(find_qa_empresas(country, rubro))

    if request.method == "POST":
        empresa_id = request.POST.get("empresa_id")
        empresa = None
        if empresa_id:
            empresa = next((item for item in candidates if str(item.pk) == str(empresa_id)), None)
        elif candidates:
            empresa = candidates[0]

        if not empresa:
            error = f"No existe tenant QA para {country or 'PAIS'} / {rubro or 'RUBRO'}"
            clear_qa_control_context(request)
        elif not set_qa_control_context(request, empresa):
            error = "El tenant QA no coincide con país y rubro"
            clear_qa_control_context(request)
        else:
            messages.success(request, f"Contexto QA activo: {empresa.nombre_taller}")
            return redirect("qa_control:control")

    return render(
        request,
        "qa_control/control.html",
        {
            "qa_context": selected if error is None else None,
            "qa_empresa": resolve_qa_empresa(request),
            "countries": _countries(),
            "rubros": _rubros(),
            "candidates": candidates,
            "selected_country": country,
            "selected_rubro": rubro,
            "qa_error": error,
        },
    )


@control_tower_required
@require_POST
def exit_control(request):
    clear_qa_control_context(request)
    messages.success(request, "Contexto QA cerrado. Empresa normal restaurada.")
    return redirect("qa_control:control")
