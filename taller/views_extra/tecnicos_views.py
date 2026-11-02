from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render

from taller.forms.tecnico import TecnicoForm
from taller.models import Empresa, Tecnico
from taller.models.team_member import TeamMember


def _empresa_activa(request):
    eid = request.session.get("empresa_id") or request.GET.get("empresa_id")
    qs = Empresa.objects.filter(user=request.user)
    if eid:
        qs = qs.filter(id=eid)
    return qs.order_by("id").first()


def _team_member_names(empresa):
    """Names of active team members registered in settings, excluding already-linked tecnicos."""
    linked_names = set(
        Tecnico.objects.filter(empresa=empresa).values_list("nombre", flat=True)
    )
    members = (
        TeamMember.objects.filter(empresa=empresa, is_active=True)
        .select_related("user")
        .order_by("user__first_name", "user__last_name")
    )
    return [
        m.user.get_full_name() or m.user.username
        for m in members
        if (m.user.get_full_name() or m.user.username) not in linked_names
    ]


@login_required
def tecnicos_lista(request):
    empresa = _empresa_activa(request)
    tecnicos = Tecnico.objects.filter(empresa=empresa).order_by("-activo", "nombre")
    return render(request, "tecnicos/lista.html", {"empresa": empresa, "tecnicos": tecnicos})


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
            return redirect("taller:tecnicos:lista")
    else:
        form = TecnicoForm()
    return render(
        request,
        "tecnicos/form.html",
        {
            "form": form,
            "empresa": empresa,
            "modo": "crear",
            "team_member_names": _team_member_names(empresa),
        },
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
            return redirect("taller:tecnicos:lista")
    else:
        form = TecnicoForm(instance=t)
    return render(
        request,
        "tecnicos/form.html",
        {
            "form": form,
            "empresa": empresa,
            "modo": "editar",
            "team_member_names": _team_member_names(empresa),
        },
    )


@login_required
@transaction.atomic
def tecnicos_toggle_activo(request, tecnico_id):
    empresa = _empresa_activa(request)
    t = get_object_or_404(Tecnico, id=tecnico_id, empresa=empresa)
    t.activo = not t.activo
    t.save(update_fields=["activo"])
    messages.success(request, f"Técnico {'activado' if t.activo else 'desactivado'}.")
    return redirect("taller:tecnicos:lista")
