from django.contrib.auth.decorators import login_required
from django.http import JsonResponse

from taller.models.repuesto import Repuesto
from taller.models.sequence import DocumentSequence
from taller.models.vehiculos import Vehiculo


@login_required
def api_vehiculos_por_cliente(request):
    """API para obtener vehículos de un cliente específico"""
    cid = request.GET.get("cliente_id")
    qs = Vehiculo.objects.none()
    if cid:
        qs = Vehiculo.objects.filter(cliente_id=cid, empresa=request.user.empresa).values(
            "id", "patente", "vin", "marca__nombre", "modelo__nombre"
        )
    return JsonResponse(list(qs), safe=False)


@login_required
def api_repuesto_por_codigo(request):
    """API para obtener repuesto por código"""
    code = request.GET.get("codigo", "").strip()
    data = {}
    if code:
        try:
            r = Repuesto.objects.get(empresa=request.user.empresa, part_number__iexact=code)
            data = {
                "id": r.id,
                "nombre": r.nombre,
                "precio_compra": str(r.precio_compra or 0),
                "precio_venta": str(r.precio_venta or 0),
            }
        except Repuesto.DoesNotExist:
            data = {"id": None}
    return JsonResponse(data)


@login_required
def api_next_number(request):
    """API para obtener el siguiente número de documento"""
    tipo = request.GET.get("tipo", "").strip()
    data = {"numero": "Se generará automáticamente"}

    if tipo:
        try:
            # Obtener el siguiente número sin incrementarlo aún
            sequence, created = DocumentSequence.objects.get_or_create(
                empresa=request.user.empresa, tipo=tipo, defaults={"current": 0}
            )

            # Generar el número con el siguiente valor
            next_num = sequence.current + 1
            prefix = {"OT": "OT", "FAC": "F", "PRES": "P"}.get(tipo, "D")
            numero = f"{prefix}{next_num:03d}"

            data = {"numero": numero}
        except Exception as e:
            print(f"Error generando número: {e}")
            data = {"numero": f"Se generará automáticamente ({tipo})"}

    return JsonResponse(data)


import json

from django.db import transaction
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods


def _get_company_settings(emp):
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
    if "user" in fields and hasattr(emp, "user_id"):
        return qs.filter(user=emp.user).first()
    return None


def _tax_rate_for_empresa(emp):
    """
    Intenta leer tasa desde CompanySettings:
    - si el campo está en [iva, iva_porcentaje, sales_tax, tax_rate, tasa_iva]
      interpreta: valores >1 como porcentaje (19 => 0.19), valores <=1 como fracción (0.19).
    - fallback: 19% en CL, 0% fuera.
    """
    cs = _get_company_settings(emp)
    if cs:
        for name in ("iva", "iva_porcentaje", "sales_tax", "tax_rate", "tasa_iva"):
            if hasattr(cs, name):
                try:
                    val = float(getattr(cs, name))
                except (TypeError, ValueError):
                    continue
                if val < 0:
                    continue
                return val / 100.0 if val > 1 else val
    return 0.19 if (getattr(emp, "pais", "") or "").upper() == "CL" else 0.0


@csrf_exempt
@require_http_methods(["POST"])
@transaction.atomic
def api_create(request):
    try:
        payload = json.loads((request.body or b"").decode("utf-8"))
    except json.JSONDecodeError:
        return JsonResponse({"error": "malformed_json"}, status=400)

    required = ["empresa_id", "cliente_id", "vehiculo_id", "tipo", "fecha_emision"]
    missing = [k for k in required if k not in payload]
    if missing:
        return JsonResponse({"error": "missing_fields", "fields": missing}, status=400)

    from taller.models.clientes import Cliente
    from taller.models.documento import Documento
    from taller.models.empresa import Empresa
    from taller.models.lineas_documento import LineaRepuesto, LineaServicio
    from taller.models.vehiculos import Vehiculo

    # FKs
    try:
        emp = Empresa.objects.get(id=payload["empresa_id"])
    except Empresa.DoesNotExist:
        return JsonResponse({"error": "empresa_not_found"}, status=400)

    # 🔒 SEGURIDAD: Filtrar por empresa para aislamiento multi-tenant
    try:
        cli = Cliente.objects.get(id=payload["cliente_id"], empresa=emp)
    except Cliente.DoesNotExist:
        return JsonResponse({"error": "cliente_not_found"}, status=400)

    # 🔒 SEGURIDAD: Filtrar por empresa para aislamiento multi-tenant
    try:
        veh = Vehiculo.objects.get(id=payload["vehiculo_id"], empresa=emp)
    except Vehiculo.DoesNotExist:
        return JsonResponse({"error": "vehiculo_not_found"}, status=400)

    # Validación adicional de consistencia (redundante pero defensiva)
    if cli.empresa_id != emp.id or veh.empresa_id != emp.id:
        return JsonResponse({"error": "empresa_mismatch_fk"}, status=400)

    # Crear Documento (soporta proyectos con/ sin campos opcionales)
    doc_kwargs = dict(
        empresa=emp,
        tipo=payload["tipo"],
        fecha_emision=payload["fecha_emision"],
    )
    if "cliente" in [f.name for f in Documento._meta.fields]:
        doc_kwargs["cliente"] = cli
    if "vehiculo" in [f.name for f in Documento._meta.fields]:
        doc_kwargs["vehiculo"] = veh

    doc = Documento.objects.create(**doc_kwargs)

    # Si nos pasan un técnico responsable, setear en el Documento (si existe el campo)
    tecnico_obj = None
    tecnico_id = payload.get("tecnico_responsable_id")
    if tecnico_id and "tecnico_responsable" in [f.name for f in Documento._meta.fields]:
        try:
            from taller.models.tecnico import Tecnico

            tecnico_obj = Tecnico.objects.get(id=tecnico_id)
            doc.tecnico_responsable = tecnico_obj
            doc.save(update_fields=["tecnico_responsable"])
        except Exception:
            tecnico_obj = None  # si no existe el modelo/campo, lo ignoramos

    def _valid_line(d):
        try:
            return (
                str(d.get("nombre", "")).strip()
                and int(d.get("cantidad", 0)) > 0
                and float(d.get("precio_unitario", 0)) >= 0
                and float(d.get("descuento", 0)) >= 0
            )
        except Exception:
            return False

    def _responsable_kwargs(model, tecnico):
        if not tecnico:
            return {}
        # heredamos a la línea si el modelo tiene alguno de estos campos
        field_order = ["tecnico", "mecanico", "responsable", "tecnico_responsable"]
        model_fields = {f.name for f in model._meta.fields}
        for fname in field_order:
            if fname in model_fields:
                return {fname: tecnico}
        return {}

    subtotal = 0.0

    # Crear líneas de servicio
    for d in payload.get("lineas_servicio") or []:
        if not _valid_line(d):
            return JsonResponse({"error": "invalid_line_servicio"}, status=400)
        ls_kwargs = dict(
            documento=doc,
            nombre=d["nombre"],
            cantidad=int(d["cantidad"]),
            precio_unitario=float(d["precio_unitario"]),
            descuento=float(d.get("descuento", 0)),
        )
        ls_kwargs.update(_responsable_kwargs(LineaServicio, tecnico_obj))
        LineaServicio.objects.create(**ls_kwargs)
        subtotal += (ls_kwargs["cantidad"] * ls_kwargs["precio_unitario"]) - ls_kwargs["descuento"]

    # Crear líneas de repuesto
    for d in payload.get("lineas_repuesto") or []:
        if not _valid_line(d):
            return JsonResponse({"error": "invalid_line_repuesto"}, status=400)
        lr_kwargs = dict(
            documento=doc,
            nombre=d["nombre"],
            cantidad=int(d["cantidad"]),
            precio_unitario=float(d["precio_unitario"]),
            descuento=float(d.get("descuento", 0)),
        )
        # soporta 'codigo' autogenerado si tu modelo lo exige; si no existe, no lo usamos
        if "codigo" in [f.name for f in LineaRepuesto._meta.fields]:
            if d.get("codigo"):
                lr_kwargs["codigo"] = d["codigo"]
            else:
                lr_kwargs["codigo"] = f"REP-{doc.id}-{d['nombre'][:8]}".upper()
        lr_kwargs.update(_responsable_kwargs(LineaRepuesto, tecnico_obj))
        LineaRepuesto.objects.create(**lr_kwargs)
        subtotal += (lr_kwargs["cantidad"] * lr_kwargs["precio_unitario"]) - lr_kwargs["descuento"]

    # Cálculo de impuesto usando CompanySettings con fallback
    tasa = _tax_rate_for_empresa(emp)
    iva = round(subtotal * tasa, 2)
    total = round(subtotal + iva, 2)

    data = {
        "id": doc.id,
        "tipo": doc.tipo,
        "fecha_emision": str(doc.fecha_emision),
        "subtotal": round(subtotal, 2),
        "iva": iva,
        "total": total,
    }
    return JsonResponse({"documento": data}, status=201)
