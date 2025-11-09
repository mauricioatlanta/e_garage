"""
API endpoints para documentos - Versión Segura y Multi-Tenant
Corrige: seguridad, IVA solo sobre repuestos, precisión Decimal, numeración segura
"""

import json
from decimal import ROUND_HALF_UP, Decimal

from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_GET, require_POST

from taller.models.repuesto import Repuesto
from taller.models.sequence import DocumentSequence
from taller.models.vehiculos import Vehiculo


def _json_ok(data, status=200):
    """Helper para respuestas JSON consistentes"""
    return JsonResponse(data, status=status, safe=isinstance(data, dict))


def _to_dec(x, default="0"):
    """Convierte a Decimal con manejo de errores"""
    try:
        return (Decimal(str(x)) if x is not None else Decimal(default)).quantize(
            Decimal("0.01")
        )
    except Exception:
        return Decimal(default)


def _round2(x: Decimal) -> Decimal:
    """Redondeo bancario a 2 decimales"""
    return x.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


@login_required
@require_GET
def api_vehiculos_por_cliente(request):
    """API para obtener vehículos de un cliente específico (scoped a la empresa del usuario)."""
    cid = request.GET.get("cliente_id")
    try:
        cid = int(cid)
    except (TypeError, ValueError):
        return _json_ok([], 200)

    qs = (
        Vehiculo.objects.filter(cliente_id=cid, empresa=request.user.empresa)
        .select_related("marca", "modelo")
        .values(
            "id",
            "patente",
            "vin",
            "anio",
            "marca__nombre",
            "modelo__nombre",
            "marca_texto",
            "modelo_texto",
        )
        .order_by("patente", "id")
    )
    return _json_ok(list(qs))


@login_required
@require_GET
def api_repuesto_por_codigo(request):
    """API para obtener repuesto por código (scoped a empresa)."""
    code = (request.GET.get("codigo") or "").strip()
    data = {"id": None}
    if code:
        try:
            r = Repuesto.objects.get(
                empresa=request.user.empresa, part_number__iexact=code
            )
            data = {
                "id": r.id,
                "nombre": r.nombre,
                "precio_compra": str(_round2(_to_dec(r.precio_compra))),
                "precio_venta": str(_round2(_to_dec(r.precio_venta))),
            }
        except Repuesto.DoesNotExist:
            pass
    return _json_ok(data)


@login_required
@require_GET
def api_next_number(request):
    """
    Devuelve una vista previa del siguiente número sin reservarlo.
    La reserva real debe hacerse en la creación del documento.
    """
    tipo = (request.GET.get("tipo") or "").strip().upper()
    allowed = {"OT": "OT", "PRES": "P", "REC": "R"}  # prefijos sobrios
    if tipo not in allowed:
        return _json_ok({"numero": "Se generará automáticamente"}, 200)

    seq, _ = DocumentSequence.objects.get_or_create(
        empresa=request.user.empresa, tipo=tipo, defaults={"current": 0}
    )
    next_num = (seq.current or 0) + 1
    numero = f"{allowed[tipo]}{next_num:03d}"
    return _json_ok({"numero": numero})


# === Impuestos & settings ===


def _get_company_settings(emp):
    """Obtiene configuración de la empresa con fallbacks"""
    try:
        from taller.models.company_settings import CompanySettings
    except Exception:
        return None
    fields = {f.name for f in CompanySettings._meta.fields}
    qs = CompanySettings.objects.all()
    if "empresa" in fields:
        return qs.filter(empresa=emp).first()
    if "company" in fields:
        return qs.filter(company=emp).first()
    if "user" in fields and getattr(emp, "user_id", None):
        # usar user_id si existe; getattr evita AttributeError
        return qs.filter(user_id=emp.user_id).first()
    return None


def _tax_rate_for_empresa(emp) -> Decimal:
    """
    Lee tasa desde CompanySettings si existe (iva, iva_porcentaje, sales_tax, tax_rate, tasa_iva).
    >1 como porcentaje (19 => 0.19); <=1 como fracción (0.19).
    Fallback: CL=0.19, otro país=0.00.
    """
    cs = _get_company_settings(emp)
    if cs:
        for name in ("iva", "iva_porcentaje", "sales_tax", "tax_rate", "tasa_iva"):
            if hasattr(cs, name):
                try:
                    val = Decimal(str(getattr(cs, name)))
                except Exception:
                    continue
                if val >= 0:
                    return (val / Decimal("100")) if val > 1 else val
    return (
        Decimal("0.19")
        if (getattr(emp, "pais", "") or "").upper() == "CL"
        else Decimal("0.00")
    )


# === Creación de documento ===


@login_required
@csrf_protect
@require_POST
@transaction.atomic
def api_create(request):
    """
    Crea el documento y sus líneas dentro de una transacción.
    - Enforce empresa = request.user.empresa (ignoramos empresa_id del payload si viene).
    - IVA solo sobre repuestos.
    - Opcional: heredar técnico a líneas si flag lo permite.
    - (Recomendado) Reservar correlativo aquí si tu modelo lo requiere.
    """
    try:
        payload = json.loads((request.body or b"").decode("utf-8"))
    except json.JSONDecodeError:
        return _json_ok({"error": "malformed_json"}, 400)

    required = ["cliente_id", "vehiculo_id", "tipo", "fecha_emision"]
    missing = [k for k in required if k not in payload]
    if missing:
        return _json_ok({"error": "missing_fields", "fields": missing}, 400)

    tipo = str(payload.get("tipo", "")).strip().upper()
    if tipo not in {"OT", "PRES", "REC"}:
        return _json_ok({"error": "invalid_tipo"}, 400)

    # Empresa del usuario (multi-tenant enforcement)
    from taller.models.clientes import Cliente
    from taller.models.documento import Documento
    from taller.models.empresa import Empresa
    from taller.models.lineas_documento import LineaRepuesto, LineaServicio
    from taller.models.vehiculos import Vehiculo

    emp: Empresa = request.user.empresa

    # FKs
    try:
        cli = Cliente.objects.get(id=payload["cliente_id"], empresa=emp)
    except Cliente.DoesNotExist:
        return _json_ok({"error": "cliente_not_found"}, 400)

    try:
        veh = Vehiculo.objects.get(id=payload["vehiculo_id"], empresa=emp)
    except Vehiculo.DoesNotExist:
        return _json_ok({"error": "vehiculo_not_found"}, 400)

    # Consistencia: el vehículo debe pertenecer al cliente (si tu modelo lo define así)
    if getattr(veh, "cliente_id", None) and veh.cliente_id != cli.id:
        return _json_ok({"error": "vehiculo_cliente_mismatch"}, 400)

    # Crear Documento
    doc_kwargs = dict(
        empresa=emp,
        tipo=tipo,
        fecha_emision=payload["fecha_emision"],  # ISO yyyy-mm-dd
    )
    doc_fields = {f.name for f in Documento._meta.fields}
    if "cliente" in doc_fields:
        doc_kwargs["cliente"] = cli
    if "vehiculo" in doc_fields:
        doc_kwargs["vehiculo"] = veh

    doc = Documento.objects.create(**doc_kwargs)

    # (Opcional recomendado) Reservar y asignar correlativo aquí de manera segura
    # si tu Documento tiene un campo 'numero'
    if "numero" in doc_fields:
        seq = DocumentSequence.objects.select_for_update().get_or_create(
            empresa=emp, tipo=tipo, defaults={"current": 0}
        )[0]
        seq.current = (seq.current or 0) + 1
        seq.save(update_fields=["current"])
        prefix = {"OT": "OT", "PRES": "P", "REC": "R"}[tipo]
        doc.numero = f"{prefix}{seq.current:03d}"
        doc.save(update_fields=["numero"])

    # Técnico responsable (si aplica)
    tecnico_obj = None
    tecnico_id = payload.get("tecnico_responsable_id")
    if tecnico_id and "tecnico_responsable" in doc_fields:
        try:
            from taller.models.tecnico import Tecnico

            tecnico_obj = Tecnico.objects.get(id=tecnico_id, empresa=emp)
            doc.tecnico_responsable = tecnico_obj
            doc.save(update_fields=["tecnico_responsable"])
        except Exception:
            tecnico_obj = None

    # Flag para herencia de técnico a líneas (si existe y está desactivado dividir)
    cs = _get_company_settings(emp)
    split_by_tech = bool(getattr(cs, "split_by_technician", False))

    def _valid_line(d):
        try:
            return (
                str(d.get("nombre", "")).strip()
                and int(d.get("cantidad", 0)) > 0
                and _to_dec(d.get("precio_unitario", 0)) >= 0
                and _to_dec(d.get("descuento", 0)) >= 0
            )
        except Exception:
            return False

    def _responsable_kwargs(model, tecnico):
        if split_by_tech:  # si se divide por técnico, no heredamos automáticamente
            return {}
        if not tecnico:
            return {}
        field_order = ["tecnico", "mecanico", "responsable", "tecnico_responsable"]
        model_fields = {f.name for f in model._meta.fields}
        for fname in field_order:
            if fname in model_fields:
                return {fname: tecnico}
        return {}

    subtotal_serv = Decimal("0.00")
    subtotal_rep = Decimal("0.00")

    # Líneas de servicio
    for d in payload.get("lineas_servicio") or []:
        if not _valid_line(d):
            return _json_ok({"error": "invalid_line_servicio"}, 400)
        cantidad = int(d["cantidad"])
        precio = _to_dec(d["precio_unitario"])
        descuento = _to_dec(d.get("descuento", 0))
        ls_kwargs = dict(
            documento=doc,
            nombre=d["nombre"].strip(),
            cantidad=cantidad,
            precio_unitario=precio,
            descuento=descuento,
        )
        ls_kwargs.update(_responsable_kwargs(LineaServicio, tecnico_obj))
        LineaServicio.objects.create(**ls_kwargs)
        subtotal_serv += (precio * cantidad) - descuento

    # Líneas de repuesto
    for d in payload.get("lineas_repuesto") or []:
        if not _valid_line(d):
            return _json_ok({"error": "invalid_line_repuesto"}, 400)
        cantidad = int(d["cantidad"])
        precio = _to_dec(d["precio_unitario"])
        descuento = _to_dec(d.get("descuento", 0))
        lr_kwargs = dict(
            documento=doc,
            nombre=d["nombre"].strip(),
            cantidad=cantidad,
            precio_unitario=precio,
            descuento=descuento,
        )
        lr_fields = {f.name for f in LineaRepuesto._meta.fields}
        if "codigo" in lr_fields:
            lr_kwargs["codigo"] = (
                d.get("codigo") or f"REP-{doc.id}-{d['nombre'][:8]}"
            ).upper()
        lr_kwargs.update(_responsable_kwargs(LineaRepuesto, tecnico_obj))
        LineaRepuesto.objects.create(**lr_kwargs)
        subtotal_rep += (precio * cantidad) - descuento

    # Impuesto: SOLO sobre repuestos (regla CL/USA)
    tasa = _tax_rate_for_empresa(emp)
    iva = _round2(subtotal_rep * tasa)
    subtotal = _round2(subtotal_serv + subtotal_rep)
    total = _round2(subtotal + iva)

    resp = {
        "id": doc.id,
        "tipo": doc.tipo,
        "numero": getattr(doc, "numero", None),
        "fecha_emision": str(doc.fecha_emision),
        "subtotal_servicios": str(_round2(subtotal_serv)),
        "subtotal_repuestos": str(_round2(subtotal_rep)),
        "subtotal": str(subtotal),
        "iva": str(iva),
        "total": str(total),
    }
    return _json_ok({"documento": resp}, 201)
