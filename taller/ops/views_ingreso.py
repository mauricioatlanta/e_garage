"""
Vistas del flujo Centro de Ingreso Pro (ops/ingreso).
Todas las queries filtran por empresa del usuario.
"""

from decimal import Decimal

from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from taller.auth.decorators import login_required_default
from taller.forms.ops_ingreso import (
    ChecklistIngresoForm,
    DocumentoIngresoForm,
    KilometrajeForm,
    PatenteForm,
    VehiculoQuickCreateForm,
)
from taller.models import (
    Cliente,
    Documento,
    KilometrajeRegistro,
    LineaRepuesto,
    RegistroKilometraje,
    ChecklistIngreso as ChecklistIngresoModel,
    Repuesto,
    Vehiculo,
)


def _get_empresa(request):
    if not request.user.is_authenticated:
        return None
    return getattr(request.user, "empresa", None)


@login_required_default
def ops_ingreso_home(request):
    empresa = _get_empresa(request)
    if not empresa:
        messages.error(request, "Selecciona o crea tu empresa para continuar.")
        return redirect("/cl/")
    from taller.utils.ocr import is_ocr_available

    return render(
        request,
        "taller/ops/ingreso/home.html",
        {"empresa": empresa, "ocr_available": is_ocr_available()},
    )


@login_required_default
def ops_ingreso_patente(request):
    empresa = _get_empresa(request)
    if not empresa:
        messages.error(request, "Selecciona o crea tu empresa para continuar.")
        return redirect("/cl/")

    patente_val = None
    if request.method == "POST":
        form = PatenteForm(request.POST)
        if form.is_valid():
            patente_val = form.cleaned_data["patente"]
            vehiculo = Vehiculo.objects.filter(empresa=empresa, patente=patente_val).first()
            if vehiculo:
                return redirect("ops:ops_ingreso_kilometraje", vehiculo_id=vehiculo.pk)
            # No encontrado: mostrar mismo template con panel creación rápida
            return render(
                request,
                "taller/ops/ingreso/patente.html",
                {
                    "form": PatenteForm(initial={"patente": patente_val}),
                    "empresa": empresa,
                    "patente": patente_val,
                    "vehiculo": None,
                    "crear_form": VehiculoQuickCreateForm(
                        initial={"patente": patente_val, "anio": timezone.now().year},
                        empresa=empresa,
                    ),
                },
            )
    else:
        form = PatenteForm(initial={"patente": request.GET.get("patente", "")})

    return render(
        request,
        "taller/ops/ingreso/patente.html",
        {"form": form, "empresa": empresa, "patente": None, "vehiculo": None, "crear_form": None},
    )


@login_required_default
def ops_ingreso_vehiculo_crear(request):
    empresa = _get_empresa(request)
    if not empresa:
        messages.error(request, "Selecciona o crea tu empresa para continuar.")
        return redirect("/cl/")

    patente = (
        (request.GET.get("patente") or request.POST.get("patente") or "")
        .strip()
        .upper()
        .replace(" ", "")
        .replace("-", "")
    )
    cliente_id = request.GET.get("cliente_id") or (request.session.get("ops_ingreso_cliente_id"))

    if request.method == "POST":
        form = VehiculoQuickCreateForm(request.POST, empresa=empresa)
        if form.is_valid():
            data = form.cleaned_data
            cliente = data["cliente"]
            anio = data["anio"]
            if not patente:
                messages.error(request, "Falta patente.")
                return redirect("ops:ops_ingreso_home")
            vehiculo = Vehiculo.objects.create(
                empresa=empresa,
                cliente=cliente,
                patente=patente,
                anio=anio,
                marca_texto=data.get("marca_texto") or "",
                modelo_texto=data.get("modelo_texto") or "",
            )
            if request.session.get("ops_ingreso_cliente_id"):
                del request.session["ops_ingreso_cliente_id"]
            messages.success(request, f"Vehículo {patente} creado.")
            return redirect("ops:ops_ingreso_kilometraje", vehiculo_id=vehiculo.pk)
    else:
        form = VehiculoQuickCreateForm(
            initial={
                "patente": patente,
                "anio": timezone.now().year,
                "cliente": cliente_id,
            },
            empresa=empresa,
        )
        if cliente_id:
            try:
                form.fields["cliente"].initial = int(cliente_id)
            except (ValueError, TypeError):
                pass

    return render(
        request,
        "taller/ops/ingreso/vehiculo_crear.html",
        {"form": form, "empresa": empresa, "patente": patente},
    )


@login_required_default
def ops_ingreso_kilometraje(request, vehiculo_id):
    empresa = _get_empresa(request)
    if not empresa:
        messages.error(request, "Selecciona o crea tu empresa para continuar.")
        return redirect("/cl/")

    vehiculo = get_object_or_404(Vehiculo, pk=vehiculo_id, empresa=empresa)
    ultimo_km = None
    try:
        ultimo_reg = vehiculo.historial_kilometraje.first()
        if ultimo_reg:
            ultimo_km = ultimo_reg.kilometraje
    except Exception:
        pass

    if request.method == "POST":
        form = KilometrajeForm(request.POST, request.FILES)
        if form.is_valid():
            km = form.cleaned_data["kilometraje"]
            if (
                ultimo_km is not None
                and km < ultimo_km
                and not form.cleaned_data.get("confirmar_km_menor")
            ):
                messages.warning(
                    request,
                    "El kilometraje es menor al último registrado. Marque la confirmación si es correcto.",
                )
                return render(
                    request,
                    "taller/ops/ingreso/kilometraje.html",
                    {
                        "form": form,
                        "empresa": empresa,
                        "vehiculo": vehiculo,
                        "ultimo_km": ultimo_km,
                        "step": 2,
                    },
                )
            foto = form.cleaned_data.get("foto_tablero")
            motivo = (form.cleaned_data.get("omitido_motivo") or "").strip()
            if not foto and not motivo:
                messages.error(request, "Debe subir foto del tablero o indicar motivo de omisión.")
                return render(
                    request,
                    "taller/ops/ingreso/kilometraje.html",
                    {
                        "form": form,
                        "empresa": empresa,
                        "vehiculo": vehiculo,
                        "ultimo_km": ultimo_km,
                        "step": 2,
                    },
                )
            reg = RegistroKilometraje.objects.create(
                empresa=empresa,
                vehiculo=vehiculo,
                kilometraje=km,
                foto_tablero=foto or None,
                omitido_motivo=motivo or "",
                source="ingreso",
                created_by=request.user,
            )
            KilometrajeRegistro.objects.create(
                empresa=empresa,
                vehiculo=vehiculo,
                documento=None,
                kilometraje=km,
                registrado_por=None,
            )
            messages.success(request, "Kilometraje registrado.")
            return redirect("ops:ops_ingreso_documento", vehiculo_id=vehiculo.pk)
    else:
        form = KilometrajeForm(initial={"kilometraje": ultimo_km or 0})

    return render(
        request,
        "taller/ops/ingreso/kilometraje.html",
        {"form": form, "empresa": empresa, "vehiculo": vehiculo, "ultimo_km": ultimo_km, "step": 2},
    )


@login_required_default
def ops_ingreso_documento(request, vehiculo_id):
    empresa = _get_empresa(request)
    if not empresa:
        messages.error(request, "Selecciona o crea tu empresa para continuar.")
        return redirect("/cl/")

    vehiculo = get_object_or_404(Vehiculo, pk=vehiculo_id, empresa=empresa)
    cliente = vehiculo.cliente

    if request.method == "POST":
        form = DocumentoIngresoForm(request.POST)
        if form.is_valid():
            motivo = (form.cleaned_data.get("motivo") or "").strip()
            tipo = form.cleaned_data["tipo_documento"]
            doc = Documento.objects.create(
                empresa=empresa,
                cliente=cliente,
                vehiculo=vehiculo,
                tipo=tipo,
                estado="BORRADOR",
                fecha_emision=timezone.now().date(),
                observaciones=motivo or None,
            )
            messages.success(request, f"Documento {doc.numero_documento} creado en borrador.")
            return redirect("ops:ops_ingreso_checklist", documento_id=doc.pk)
    else:
        form = DocumentoIngresoForm(initial={"tipo_documento": "OT"})

    return render(
        request,
        "taller/ops/ingreso/documento.html",
        {"form": form, "empresa": empresa, "vehiculo": vehiculo, "cliente": cliente, "step": 3},
    )


@login_required_default
def ops_ingreso_checklist(request, documento_id):
    empresa = _get_empresa(request)
    if not empresa:
        messages.error(request, "Selecciona o crea tu empresa para continuar.")
        return redirect("/cl/")

    documento = get_object_or_404(Documento, pk=documento_id, empresa=empresa)

    if request.method == "POST":
        form = ChecklistIngresoForm(request.POST, request.FILES)
        if form.is_valid():
            checklist, _ = ChecklistIngresoModel.objects.get_or_create(
                documento=documento,
                defaults={
                    "nivel_combustible": form.cleaned_data.get("nivel_combustible", 0),
                    "luces_funcionan": form.cleaned_data.get("luces_funcionan", True),
                    "objetos_valor": form.cleaned_data.get("objetos_valor", ""),
                },
            )
            for key in ("foto_frontal", "foto_trasera", "foto_lateral_1", "foto_lateral_2"):
                f = form.cleaned_data.get(key)
                if f:
                    setattr(checklist, key, f)
            checklist.save()
            messages.success(request, "Checklist guardado.")
            return redirect("ops:ops_ingreso_repuestos", documento_id=documento.pk)
    else:
        try:
            c = documento.checklist_ingreso
            form = ChecklistIngresoForm(
                initial={
                    "nivel_combustible": c.nivel_combustible,
                    "luces_funcionan": c.luces_funcionan,
                    "objetos_valor": c.objetos_valor,
                }
            )
            danos_json = c.danos or {}
        except ChecklistIngresoModel.DoesNotExist:
            form = ChecklistIngresoForm()
            danos_json = {}

    return render(
        request,
        "taller/ops/ingreso/checklist.html",
        {
            "form": form,
            "empresa": empresa,
            "documento": documento,
            "step": 4,
            "danos_json": danos_json,
        },
    )


@login_required_default
def ops_ingreso_repuestos(request, documento_id):
    empresa = _get_empresa(request)
    if not empresa:
        messages.error(request, "Selecciona o crea tu empresa para continuar.")
        return redirect("/cl/")

    documento = get_object_or_404(Documento, pk=documento_id, empresa=empresa)
    lineas = documento.lineas_repuesto.all().select_related("repuesto")

    return render(
        request,
        "taller/ops/ingreso/repuestos.html",
        {"empresa": empresa, "documento": documento, "lineas": lineas, "step": 5},
    )
