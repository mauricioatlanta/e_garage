from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render

from taller.forms.tecnico import TecnicoForm
from taller.models import Empresa, Tecnico


def _empresa_activa(request):
    eid = request.session.get("empresa_id") or request.GET.get("empresa_id")
    qs = Empresa.objects.filter(user=request.user)
    if eid:
        qs = qs.filter(id=eid)
    return qs.order_by("id").first()


@login_required
def tecnicos_lista(request):
    empresa = _empresa_activa(request)
    tecnicos = Tecnico.objects.filter(empresa=empresa).order_by("-activo", "nombre")
    return render(
        request, "tecnicos/lista.html", {"empresa": empresa, "tecnicos": tecnicos}
    )


@login_required
@transaction.atomic
def tecnicos_crear(request):
    empresa = _empresa_activa(request)
    if request.method == "POST":
        form = TecnicoForm(request.POST)
        if form.is_valid():
            t = form.save(commit=False)
            t.empresa = empresa
            t.save()
            messages.success(request, "Técnico creado.")
            return redirect("taller:tecnicos_lista")
    else:
        form = TecnicoForm()
    return render(
        request,
        "tecnicos/form.html",
        {"form": form, "empresa": empresa, "modo": "crear"},
    )


@login_required
@transaction.atomic
def tecnicos_editar(request, tecnico_id):
    empresa = _empresa_activa(request)
    t = get_object_or_404(Tecnico, id=tecnico_id, empresa=empresa)
    if request.method == "POST":
        form = TecnicoForm(request.POST, instance=t)
        if form.is_valid():
            form.save()
            messages.success(request, "Técnico actualizado.")
            return redirect("taller:tecnicos_lista")
    else:
        form = TecnicoForm(instance=t)
    return render(
        request,
        "tecnicos/form.html",
        {"form": form, "empresa": empresa, "modo": "editar"},
    )


@login_required
@transaction.atomic
def tecnicos_toggle_activo(request, tecnico_id):
    empresa = _empresa_activa(request)
    t = get_object_or_404(Tecnico, id=tecnico_id, empresa=empresa)
    t.activo = not t.activo
    t.save(update_fields=["activo"])
    messages.success(request, f"Técnico {'activado' if t.activo else 'desactivado'}.")
    return redirect("taller:tecnicos_lista")
