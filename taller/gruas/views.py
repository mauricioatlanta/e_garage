from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods

from taller.auth.decorators import country_login_required
from taller.gruas.forms import TowingAssignmentForm, TowingEvidenceForm, TowingLedgerForm, TowingOrderForm, TowingQuoteForm
from taller.gruas.permissions import ensure_order_access, empresa_del_request
from taller.gruas.services.assignment_service import assign_order
from taller.gruas.services.financial_service import add_entry, financial_summary
from taller.gruas.services.order_service import accept_quote, create_quote, transition_order
from taller.models import TowingAssignment, TowingDriver, TowingEvidence, TowingOrder, TowingUnit
from taller.templatetags.country_url import reverse_country_url


def _empresa(request):
    return empresa_del_request(request)


@country_login_required
def dispatch_board(request):
    empresa = _empresa(request)
    orders = TowingOrder.objects.filter(empresa=empresa).prefetch_related("assignments", "quotes").order_by("-created_at")
    return render(request, "taller/gruas/dispatch_board.html", {"orders": orders})


@country_login_required
@require_http_methods(["GET", "POST"])
def order_create(request):
    empresa = _empresa(request)
    form = TowingOrderForm(request.POST or None, empresa=empresa)
    if form.is_valid():
        order = form.save(commit=False)
        order.empresa = empresa
        order.numero = f"GR-{empresa.towing_orders.count() + 1:06d}"
        order.created_by = request.user
        order.currency = getattr(empresa, "moneda", None) or "CLP"
        order.save()
        messages.success(request, "Orden de traslado creada")
        return redirect(reverse_country_url(request, "gruas:order_detail", order.id))
    return render(request, "taller/gruas/order_form.html", {"form": form})


@country_login_required
@require_http_methods(["GET", "POST"])
def order_detail(request, order_id):
    empresa = _empresa(request)
    order = get_object_or_404(TowingOrder.objects.prefetch_related("quotes", "events", "ledger_entries", "evidences", "assignments"), id=order_id, empresa=empresa)
    if request.method == "POST":
        action = request.POST.get("action")
        try:
            if action == "quote":
                form = TowingQuoteForm(request.POST)
                if form.is_valid():
                    create_quote(order_id=order.id, empresa=empresa, user=request.user, **form.cleaned_data)
                    messages.success(request, "Nueva versión de cotización creada")
            elif action == "accept_quote":
                accept_quote(quote_id=int(request.POST["quote_id"]), empresa=empresa, user=request.user)
            elif action == "transition":
                transition_order(order_id=order.id, empresa=empresa, to_status=request.POST["to_status"], user=request.user, comment=request.POST.get("comment", ""))
            elif action == "assign":
                form = TowingAssignmentForm(request.POST, empresa=empresa)
                if form.is_valid():
                    assign_order(order_id=order.id, empresa=empresa, user=request.user, **form.cleaned_data)
            elif action == "ledger":
                form = TowingLedgerForm(request.POST)
                if form.is_valid():
                    add_entry(order_id=order.id, empresa=empresa, currency=order.currency, user=request.user, **form.cleaned_data)
            elif action == "evidence" and request.FILES.get("file"):
                assignment = order.assignments.filter(is_active=True).first()
                TowingEvidence.objects.create(order=order, assignment=assignment, kind=request.POST.get("kind", "GENERAL"), file=request.FILES["file"], description=request.POST.get("description", ""), created_by=request.user)
        except Exception as exc:
            messages.error(request, str(exc))
        return redirect(reverse_country_url(request, "gruas:order_detail", order.id))
    return render(request, "taller/gruas/order_detail.html", {"order": order, "quote_form": TowingQuoteForm(), "ledger_form": TowingLedgerForm(), "assignment_form": TowingAssignmentForm(empresa=empresa), "summary": financial_summary(order)})


@country_login_required
def driver_home(request):
    empresa = _empresa(request)
    orders = TowingOrder.objects.filter(empresa=empresa, assignments__driver__user=request.user, assignments__is_active=True).distinct().order_by("planned_start_at")
    return render(request, "taller/gruas/driver_home.html", {"orders": orders})


@country_login_required
@require_http_methods(["POST"])
def driver_update(request, order_id):
    empresa = _empresa(request)
    order = get_object_or_404(TowingOrder, id=order_id, empresa=empresa)
    ensure_order_access(request, order, driver_only=True)
    transition_order(order_id=order.id, empresa=empresa, to_status=request.POST["to_status"], user=request.user, comment=request.POST.get("comment", ""))
    return redirect(reverse_country_url(request, "gruas:driver_home"))


@country_login_required
@require_http_methods(["POST"])
def driver_evidence_upload(request, order_id):
    """Accept a private photo only from the conductor's active assignment."""
    empresa = _empresa(request)
    order = get_object_or_404(TowingOrder, id=order_id, empresa=empresa)
    ensure_order_access(request, order, driver_only=True)
    assignment = order.assignments.filter(
        driver__user=request.user, is_active=True,
    ).select_related("driver").first()
    if assignment is None:
        raise PermissionDenied("La orden no está asignada activamente a este conductor")

    form = TowingEvidenceForm(request.POST, request.FILES)
    if form.is_valid():
        TowingEvidence.objects.create(
            order=order,
            assignment=assignment,
            kind=form.cleaned_data["kind"],
            file=form.cleaned_data["file"],
            description=form.cleaned_data["description"],
            created_by=request.user,
        )
        messages.success(request, "Foto guardada como evidencia privada.")
    else:
        for error in form.errors.get_json_data().values():
            for item in error:
                messages.error(request, item["message"])
    return redirect(reverse_country_url(request, "gruas:driver_home"))


@country_login_required
def evidence_download(request, evidence_id):
    empresa = _empresa(request)
    evidence = get_object_or_404(TowingEvidence.objects.select_related("order"), id=evidence_id, order__empresa=empresa)
    ensure_order_access(request, evidence.order, driver_only=not request.user.groups.filter(name__in=["Owner", "Admin"]).exists())
    if not evidence.file:
        raise Http404
    return FileResponse(evidence.file.open("rb"), as_attachment=True, filename=evidence.file.name.rsplit("/", 1)[-1])


@country_login_required
def units(request):
    empresa = _empresa(request)
    return render(request, "taller/gruas/units.html", {"units": TowingUnit.objects.filter(empresa=empresa), "drivers": TowingDriver.objects.filter(empresa=empresa, activo=True)})
