# Vistas del Inventario Inteligente y flujo real de venta (sesión → confirmar → finalizar).

import json
from decimal import Decimal, InvalidOperation

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import F
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import NoReverseMatch, reverse
from django.utils import timezone
from django.utils.translation import get_language
from django.views.decorators.http import require_GET, require_http_methods, require_POST

from taller.models.clientes import Cliente
from taller.models.correlativo import CorrelativoDocumento
from taller.models.documento import Documento
from taller.models.lineas_documento import LineaRepuesto, ORIGEN_DESARME
from taller.models.pieza_desarme import ESTADO_DISPONIBLE, ESTADO_RESERVADA, PiezaDesarme
from taller.models.vehiculo_desarme import VehiculoDesarme

from .forms_venta_inventario import ConfirmarVentaDesdeInventarioForm
from .views import _desarme_url, _empresa_or_redirect

VENTA_SESSION_KEY = "venta_desde_inventario"


@login_required
@require_GET
def inventario_inteligente(request, pk):
    """Vista del inventario inteligente (grid + drawer + búsqueda) para un vehículo de desarme."""
    empresa = _empresa_or_redirect(request)
    if not empresa:
        return redirect("/")

    vehiculo = get_object_or_404(
        VehiculoDesarme,
        pk=pk,
        empresa=empresa,
    )

    piezas_qs = (
        vehiculo.piezas_desarme.filter(activo=True)
        .prefetch_related("names", "company_labels")
        .order_by("zona", "codigo")
    )

    empresa = _empresa_or_redirect(request)
    lang = (getattr(request, "LANGUAGE_CODE", None) or get_language() or "es")[:2]
    repuestos_payload = []
    for p in piezas_qs:
        repuestos_payload.append(
            {
                "id": p.pk,
                "nombre": p.get_display_label(empresa=empresa, language=lang),
                "search_terms": p.get_search_terms(empresa=empresa, language=lang),
                "sku": p.codigo or str(p.pk),
                "categoria": p.zona or "General",
                "ubicacion": getattr(p, "ubicacion_fisica", None) or "",
                "precio": float(p.precio_venta_sugerido or 0),
                "stock": int(p.cantidad or 0),
                "vehiculo": str(vehiculo),
                "imagen": "",
                "estado_pieza": p.estado_pieza,
                "vendible": (
                    p.activo
                    and p.cantidad > 0
                    and p.estado_pieza in (ESTADO_DISPONIBLE, ESTADO_RESERVADA)
                ),
            }
        )

    context = {
        "vehiculo": vehiculo,
        "repuestos_json": json.dumps(repuestos_payload, ensure_ascii=False),
    }
    return render(
        request,
        "taller/desarme/inventario_inteligente.html",
        context,
    )


@login_required
@require_http_methods(["GET", "POST"])
def crear_venta_desde_inventario(request, pk):
    """
    Recibe selected_data (JSON) del inventario inteligente, valida stock,
    guarda en sesión y redirige a la pantalla de confirmación (cliente + revisar líneas).
    """
    empresa = _empresa_or_redirect(request)
    if not empresa:
        return redirect("/")

    vehiculo = get_object_or_404(
        VehiculoDesarme,
        pk=pk,
        empresa=empresa,
    )

    if request.method == "GET":
        messages.info(request, "Para crear la venta debes seleccionar piezas desde el inventario.")
        return redirect(_desarme_url(request, f"vehiculos/{vehiculo.pk}/inventario-inteligente/"))

    selected_data_raw = request.POST.get("selected_data", "[]")
    try:
        selected_data = json.loads(selected_data_raw)
    except json.JSONDecodeError:
        selected_data = []

    if not selected_data:
        messages.warning(request, "No se seleccionaron piezas para la venta.")
        return redirect(_desarme_url(request, f"vehiculos/{vehiculo.pk}/inventario-inteligente/"))

    lang = (getattr(request, "LANGUAGE_CODE", None) or get_language() or "es")[:2]

    valid_estados = {ESTADO_DISPONIBLE, ESTADO_RESERVADA}
    piezas_qs = PiezaDesarme.objects.filter(
        pk__in=[row.get("id") for row in selected_data if row.get("id")],
        empresa=empresa,
        vehiculo_desarme=vehiculo,
        activo=True,
        estado_pieza__in=valid_estados,
        cantidad__gt=0,
    )
    piezas_by_id = {p.pk: p for p in piezas_qs}

    seleccion_valida = []
    for row in selected_data:
        pieza_id = row.get("id")
        if not pieza_id:
            continue
        try:
            pieza_id = int(pieza_id)
        except (TypeError, ValueError):
            continue
        try:
            cantidad = int(row.get("cantidad", 1))
        except (TypeError, ValueError):
            cantidad = 1
        if cantidad < 1:
            cantidad = 1
        try:
            precio_venta = Decimal(str(row.get("precio_venta", 0)))
        except (InvalidOperation, TypeError, ValueError):
            precio_venta = Decimal("0")
        if precio_venta < 0:
            precio_venta = Decimal("0")

        pieza = piezas_by_id.get(pieza_id)
        if not pieza:
            continue
        stock_actual = int(pieza.cantidad or 0)
        if cantidad > stock_actual:
            display_nombre = pieza.get_display_label(empresa=empresa, language=lang) or pieza.nombre
            messages.warning(
                request,
                f"'{display_nombre}' no tiene stock suficiente. Disponible: {stock_actual}.",
            )
            continue

        seleccion_valida.append(
            {
                "id": pieza_id,
                "cantidad": cantidad,
                "precio_venta": str(precio_venta),
            }
        )

    if not seleccion_valida:
        messages.error(
            request,
            "No se pudo preparar ninguna línea válida para la venta.",
        )
        return redirect(_desarme_url(request, f"vehiculos/{vehiculo.pk}/inventario-inteligente/"))

    request.session[VENTA_SESSION_KEY] = {
        "vehiculo_id": vehiculo.pk,
        "items": seleccion_valida,
    }
    request.session.modified = True

    return redirect(
        _desarme_url(request, f"vehiculos/{vehiculo.pk}/confirmar-venta-desde-inventario/")
    )


def _get_venta_session_data(request, vehiculo):
    """Construye el resumen de la venta desde la sesión (items con pieza, cantidades, totales)."""
    raw = request.session.get(VENTA_SESSION_KEY) or {}
    if raw.get("vehiculo_id") != vehiculo.pk:
        return None

    items = raw.get("items") or []
    if not items:
        return None

    ids = [row["id"] for row in items if "id" in row]
    empresa = getattr(request.user, "empresa", None) if getattr(request, "user", None) else None
    piezas_qs = PiezaDesarme.objects.filter(
        empresa=empresa,
        vehiculo_desarme=vehiculo,
        pk__in=ids,
    ).prefetch_related("names", "company_labels")
    piezas = {p.pk: p for p in piezas_qs}
    lang = (getattr(request, "LANGUAGE_CODE", None) or get_language() or "es")[:2]

    resumen = []
    subtotal = Decimal("0")

    for row in items:
        pieza = piezas.get(row["id"])
        if not pieza:
            continue
        try:
            cantidad = int(row.get("cantidad", 1))
        except (TypeError, ValueError):
            cantidad = 1
        if cantidad < 1:
            cantidad = 1
        try:
            precio_venta = Decimal(str(row.get("precio_venta", "0")))
        except (InvalidOperation, TypeError, ValueError):
            precio_venta = Decimal("0")
        if precio_venta < 0:
            precio_venta = Decimal("0")

        stock_actual = int(pieza.cantidad or 0)
        linea_total = Decimal(cantidad) * precio_venta
        subtotal += linea_total
        display_nombre = (
            pieza.get_display_label(empresa=empresa, language=lang)
            if empresa
            else (pieza.nombre or "")
        )

        resumen.append(
            {
                "repuesto": pieza,
                "display_nombre": display_nombre,
                "cantidad": cantidad,
                "precio_venta": precio_venta,
                "stock_actual": stock_actual,
                "linea_total": linea_total,
            }
        )

    if not resumen:
        return None

    return {
        "vehiculo": vehiculo,
        "items": resumen,
        "subtotal": subtotal,
        "total_items": len(resumen),
        "total_unidades": sum(x["cantidad"] for x in resumen),
    }


def _default_tax_id_type(empresa):
    """Devuelve el tipo de identificador tributario por defecto según país de la empresa."""
    pais = (getattr(empresa, "pais", None) or "CL").upper()
    return {
        "CL": "CL_RUT",
        "US": "US_SSN",
        "BR": "BR_CPF",
        "PE": "PE_RUC",
        "VE": "VE_RIF",
        "MX": "MX_RFC",
    }.get(pais, "CL_RUT")


def _crear_o_reusar_cliente_rapido(empresa, form):
    """
    Crea un cliente nuevo con los datos del bloque "cliente rápido" o reutiliza uno existente
    por empresa + nombre + tax_id si coincide.
    """
    nombre = (form.cleaned_data.get("cliente_nombre") or "").strip()
    tax_id_raw = (form.cleaned_data.get("cliente_rut") or "").strip()
    telefono = (form.cleaned_data.get("cliente_telefono") or "").strip()
    email = (form.cleaned_data.get("cliente_email") or "").strip()
    direccion = (form.cleaned_data.get("cliente_direccion") or "").strip()

    if not nombre:
        raise ValueError("Nombre de cliente rápido vacío.")

    tax_id_type = _default_tax_id_type(empresa)

    # Reutilizar por empresa + nombre + tax_id si existe
    if tax_id_raw:
        existing = Cliente.objects.filter(
            empresa=empresa,
            nombre=nombre,
            tax_id=tax_id_raw,
        ).first()
        if existing:
            updated = False
            if telefono and not (getattr(existing, "telefono", None) or "").strip():
                existing.telefono = telefono
                updated = True
            if email and not (getattr(existing, "email", None) or "").strip():
                existing.email = email
                updated = True
            if direccion and not (getattr(existing, "direccion", None) or "").strip():
                existing.direccion = direccion
                updated = True
            if updated:
                existing.save()
            return existing

    # Crear nuevo cliente
    cliente = Cliente(
        empresa=empresa,
        nombre=nombre,
        apellido="",
        tax_id_type=tax_id_type,
    )
    if tax_id_raw:
        cliente.tax_id = tax_id_raw
    if telefono:
        cliente.telefono = telefono
    if email:
        cliente.email = email
    if direccion:
        cliente.direccion = direccion
    cliente.save()
    return cliente


def _get_tipo_documento_por_pais(empresa):
    """Devuelve el tipo de documento comercial por país: US → invoice, Chile/otros → recibo."""
    country = getattr(empresa, "country", None) or getattr(empresa, "pais", None)
    if country == "US":
        return "invoice"
    return "recibo"


def _get_prefijo_documento(tipo):
    """Prefijo del número: INV (USA) o REC (Chile/otros)."""
    return "INV" if tipo == "invoice" else "REC"


def _generar_numero_documento(empresa, tipo):
    """
    Genera el próximo número correlativo por empresa y tipo (recibo | invoice).
    REC-000001 / INV-000001. Thread-safe con select_for_update().
    """
    with transaction.atomic():
        correlativo, _ = CorrelativoDocumento.objects.select_for_update().get_or_create(
            empresa=empresa,
            tipo=tipo,
            defaults={"ultimo_numero": 0},
        )
        correlativo.ultimo_numero += 1
        correlativo.save(update_fields=["ultimo_numero"])
        prefijo = _get_prefijo_documento(tipo)
        return f"{prefijo}-{correlativo.ultimo_numero:06d}"


def _redirect_to_documento_or_fallback(documento, vehiculo):
    """
    Intenta redirigir al panel de impresión o a la vista del documento.
    Si no existe una ruta conocida, redirige al inventario inteligente del vehículo.
    """
    candidates = [
        ("documentos:imprimir_documento", [documento.pk]),
        ("documentos:ver_documento", [documento.pk]),
        ("documentos:ver_documento_cbv", [documento.pk]),
        ("documentos:detalle_documento", [documento.pk]),
        ("documentos:detalle", [documento.pk]),
        ("taller:ver_documento", [documento.pk]),
        ("taller:detalle_documento", [documento.pk]),
    ]
    for viewname, args in candidates:
        try:
            url = reverse(viewname, args=args)
            return redirect(url)
        except NoReverseMatch:
            continue
    return redirect(_desarme_url(request, f"vehiculos/{vehiculo.pk}/inventario-inteligente/"))


@login_required
@require_GET
def confirmar_venta_desde_inventario(request, pk):
    """Pantalla de confirmación: elegir cliente, revisar líneas y confirmar."""
    empresa = _empresa_or_redirect(request)
    if not empresa:
        return redirect("/")

    vehiculo = get_object_or_404(
        VehiculoDesarme,
        pk=pk,
        empresa=empresa,
    )

    resumen = _get_venta_session_data(request, vehiculo)
    if not resumen:
        messages.error(request, "No hay una selección activa para confirmar.")
        return redirect(_desarme_url(request, f"vehiculos/{vehiculo.pk}/inventario-inteligente/"))

    form = ConfirmarVentaDesdeInventarioForm(empresa=empresa)
    tipo_doc = _get_tipo_documento_por_pais(empresa)
    tipo_doc_label = "Invoice" if tipo_doc == "invoice" else "Recibo"

    context = {
        "vehiculo": vehiculo,
        "form": form,
        "resumen": resumen,
        "empresa": empresa,
        "tipo_doc_label": tipo_doc_label,
    }
    return render(
        request,
        "taller/desarme/confirmar_venta_desde_inventario.html",
        context,
    )


@login_required
@require_POST
def finalizar_venta_desde_inventario(request, pk):
    """Crea el documento de venta, líneas de repuesto (pieza_desarme), descuenta stock y limpia sesión."""
    empresa = _empresa_or_redirect(request)
    if not empresa:
        return redirect("/")

    vehiculo = get_object_or_404(
        VehiculoDesarme,
        pk=pk,
        empresa=empresa,
    )

    resumen = _get_venta_session_data(request, vehiculo)
    if not resumen:
        messages.error(request, "No hay selección activa para finalizar.")
        return redirect(_desarme_url(request, f"vehiculos/{vehiculo.pk}/inventario-inteligente/"))

    form = ConfirmarVentaDesdeInventarioForm(request.POST, empresa=empresa)
    tipo_doc = _get_tipo_documento_por_pais(empresa)
    tipo_doc_label = "Invoice" if tipo_doc == "invoice" else "Recibo"
    if not form.is_valid():
        context = {
            "vehiculo": vehiculo,
            "form": form,
            "resumen": resumen,
            "empresa": empresa,
            "tipo_doc_label": tipo_doc_label,
        }
        return render(
            request,
            "taller/desarme/confirmar_venta_desde_inventario.html",
            context,
        )

    usar_cliente_rapido = form.cleaned_data.get("usar_cliente_rapido", False)
    try:
        if usar_cliente_rapido:
            cliente = _crear_o_reusar_cliente_rapido(empresa, form)
        else:
            cliente = form.cleaned_data["cliente"]
    except Exception as exc:
        form.add_error("cliente_nombre", f"No se pudo crear el cliente rápido: {exc}")
        context = {
            "vehiculo": vehiculo,
            "form": form,
            "resumen": resumen,
            "empresa": empresa,
            "tipo_doc_label": tipo_doc_label,
        }
        return render(
            request,
            "taller/desarme/confirmar_venta_desde_inventario.html",
            context,
        )

    observaciones = (form.cleaned_data.get("observaciones") or "").strip()

    for item in resumen["items"]:
        if item["cantidad"] > item["stock_actual"]:
            messages.error(
                request,
                f"Stock insuficiente para '{item.get('display_nombre') or item['repuesto'].nombre}'. "
                f"Disponible: {item['stock_actual']}, solicitado: {item['cantidad']}.",
            )
            return redirect(
                _desarme_url(request, f"vehiculos/{vehiculo.pk}/confirmar-venta-desde-inventario/")
            )

    tipo_doc = _get_tipo_documento_por_pais(empresa)
    with transaction.atomic():
        numero_documento = _generar_numero_documento(empresa, tipo_doc)

        # vehiculo acá siempre es un VehiculoDesarme (el corte de
        # VehiculoDesarmeForm ya no pasa por Vehiculo). Documento.vehiculo
        # exige un Vehiculo real -- usar vehiculo_desarme en su lugar,
        # dejando vehiculo=None (no hay Vehiculo legacy detrás).
        if isinstance(vehiculo, VehiculoDesarme):
            vehiculo_kwargs = {"vehiculo": None, "vehiculo_desarme": vehiculo}
        else:
            vehiculo_kwargs = {"vehiculo": vehiculo, "vehiculo_desarme": None}
        documento = Documento.objects.create(
            empresa=empresa,
            cliente=cliente,
            **vehiculo_kwargs,
            observaciones=observaciones or None,
            estado="EMITIDO",
            tipo="PTS",
            numero=numero_documento,
            fecha_emision=timezone.now().date(),
            country=getattr(empresa, "pais", "CL") or "CL",
            moneda=getattr(empresa, "moneda", "CLP") or "CLP",
        )

        for item in resumen["items"]:
            pieza = item["repuesto"]
            cantidad = item["cantidad"]
            precio_venta = item["precio_venta"]
            LineaRepuesto.objects.create(
                documento=documento,
                repuesto=None,
                part=None,
                pieza_desarme=pieza,
                codigo=pieza.codigo or "",
                nombre=pieza.nombre or "",
                cantidad=cantidad,
                precio_unitario=precio_venta,
                descuento=Decimal("0"),
                origen_repuesto=ORIGEN_DESARME,
            )

            PiezaDesarme.objects.filter(pk=pieza.pk).update(
                cantidad=F("cantidad") - cantidad,
            )

        documento.refresh_from_db()
        documento.recompute_totals(persist=True)

    request.session.pop(VENTA_SESSION_KEY, None)
    request.session.modified = True

    tipo_doc = _get_tipo_documento_por_pais(empresa)
    nombre_doc = "Invoice" if tipo_doc == "invoice" else "Recibo"
    messages.success(
        request,
        f"{nombre_doc} creado correctamente para {cliente.nombre}. #{documento.pk}",
    )

    return _redirect_to_documento_or_fallback(documento, vehiculo)
