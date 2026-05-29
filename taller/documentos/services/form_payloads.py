from __future__ import annotations

import json


def _serialize_repuesto(linea):
    return {
        "id": getattr(linea, "repuesto_id", None),
        "codigo": getattr(getattr(linea, "repuesto", None), "codigo", "") or "",
        "nombre": getattr(linea, "nombre", "")
        or getattr(getattr(linea, "repuesto", None), "nombre", "")
        or "",
        "cantidad": float(getattr(linea, "cantidad", 0) or 0),
        "precio": float(getattr(linea, "precio_unitario", 0) or 0),
        "descuento": float(getattr(linea, "descuento", 0) or 0),
        "subtotal": float(getattr(linea, "subtotal", 0) or 0),
        "origen_repuesto": getattr(linea, "origen_repuesto", None) or "STOCK_BODEGA",
        "pieza_desarme_id": getattr(linea, "pieza_desarme_id", None),
        "costo_linea": float(getattr(linea, "costo_linea", 0) or 0),
    }


def _serialize_servicio(linea):
    return {
        "id": getattr(linea, "id", None),
        "servicio_id": getattr(linea, "servicio_id", None) or getattr(linea, "service_id", None),
        "nombre": getattr(linea, "nombre", "")
        or getattr(getattr(linea, "servicio", None), "nombre", "")
        or "",
        "cantidad": float(getattr(linea, "cantidad", 0) or 0),
        "precio": float(getattr(linea, "precio_unitario", 0) or 0),
        "descuento": float(getattr(linea, "descuento", 0) or 0),
        "subtotal": float(getattr(linea, "subtotal", 0) or 0),
    }


def _serialize_otro(linea):
    return {
        "id": getattr(linea, "id", None),
        "servicio_id": getattr(linea, "servicio_id", None),
        "nombre": getattr(linea, "nombre", "")
        or getattr(getattr(linea, "servicio", None), "nombre", "")
        or "",
        "empresa_ext": getattr(linea, "empresa_externa", "") or "",
        "empresa_externa": getattr(linea, "empresa_externa", "") or "",
        "cantidad": float(getattr(linea, "cantidad", 0) or 0),
        "precio_taller": float(getattr(linea, "costo_interno", 0) or 0),
        "precio": float(getattr(linea, "precio_cliente", 0) or 0),
        "subtotal": float(
            getattr(linea, "subtotal", 0) or getattr(linea, "precio_cliente", 0) or 0
        ),
    }


def _vehicle_form_label(vehiculo):
    marca = (
        getattr(vehiculo, "marca_texto", "")
        or getattr(getattr(vehiculo, "marca", None), "nombre", "")
        or ""
    )
    modelo = (
        getattr(vehiculo, "modelo_texto", "")
        or getattr(getattr(vehiculo, "modelo", None), "nombre", "")
        or ""
    )
    patente = getattr(vehiculo, "patente", "") or getattr(vehiculo, "placa", "") or ""
    anio = getattr(vehiculo, "anio", "") or ""

    parts = [
        str(anio).strip() if anio else "",
        str(marca).strip(),
        str(modelo).strip(),
        str(patente).strip() or str(getattr(vehiculo, "vin", "") or "").strip(),
    ]
    return " - ".join(part for part in parts if part) or f"Vehículo #{vehiculo.pk}"


def _empty_line_item_payloads():
    return {
        "repuestos_json": [],
        "servicios_json": [],
        "otros_json": [],
    }


def _blank_prefetch():
    return {
        "clientes_prefetch": [],
        "vehiculos_prefetch": [],
        "repuestos_prefetch": [],
        "servicios_prefetch": [],
        "otros_servicios_prefetch": [],
    }


def _source_value(source, key, default=None):
    if source is None:
        return default
    if isinstance(source, dict):
        return source.get(key, default)
    return getattr(source, key, default)


def _safe_json_list(raw_value):
    if raw_value in (None, "", []):
        return []
    if isinstance(raw_value, list):
        return raw_value
    try:
        parsed = json.loads(raw_value)
    except (TypeError, ValueError, json.JSONDecodeError):
        return []
    return parsed if isinstance(parsed, list) else []


def _mode_value(mode):
    return getattr(mode, "mode", mode) or "clean"


def serialize_document_line_items(documento):
    if documento is None:
        return _empty_line_item_payloads()

    return {
        "repuestos_json": [_serialize_repuesto(linea) for linea in documento.lineas_repuesto.all()],
        "servicios_json": [_serialize_servicio(linea) for linea in documento.lineas_servicio.all()],
        "otros_json": [_serialize_otro(linea) for linea in documento.lineas_otro_servicio.all()],
    }


def serialize_draft_line_items(source_draft):
    return {
        "repuestos_json": _safe_json_list(_source_value(source_draft, "repuestos_json"))
        or _safe_json_list(_source_value(source_draft, "repuestos")),
        "servicios_json": _safe_json_list(_source_value(source_draft, "servicios_json"))
        or _safe_json_list(_source_value(source_draft, "servicios")),
        "otros_json": _safe_json_list(_source_value(source_draft, "otros_json"))
        or _safe_json_list(_source_value(source_draft, "otros")),
    }


def build_form_payloads(*, form_mode, documento=None):
    payload = {
        "allow_prefetch": bool(getattr(form_mode, "allow_prefetch", False)),
        "allow_line_prefill": bool(getattr(form_mode, "allow_line_prefill", False)),
        "clientes_prefetch": [],
        "vehiculos_prefetch": [],
        "repuestos_prefetch": [],
        "servicios_prefetch": [],
        "repuestos_json": "[]",
        "servicios_json": "[]",
        "otros_json": "[]",
        "document_form_bootstrap": {
            "mode": _mode_value(form_mode),
            "allow_prefetch": bool(getattr(form_mode, "allow_prefetch", False)),
            "allow_line_prefill": bool(getattr(form_mode, "allow_line_prefill", False)),
            "cliente_id": getattr(getattr(form_mode, "cliente", None), "id", None),
            "vehiculo_id": getattr(getattr(form_mode, "vehiculo", None), "id", None),
            "repuestos": [],
            "servicios": [],
            "otros_servicios": [],
        },
    }

    if getattr(form_mode, "is_clean", False) or getattr(form_mode, "is_prefill", False):
        return payload

    source_document = documento or getattr(form_mode, "source_document", None)
    if source_document is None:
        return payload

    line_item_payloads = build_line_item_payloads(mode=form_mode, source_document=source_document)
    payload["repuestos_json"] = json.dumps(line_item_payloads["repuestos_json"], ensure_ascii=False)
    payload["servicios_json"] = json.dumps(line_item_payloads["servicios_json"], ensure_ascii=False)
    payload["otros_json"] = json.dumps(line_item_payloads["otros_json"], ensure_ascii=False)
    payload["document_form_bootstrap"]["repuestos"] = line_item_payloads["repuestos_json"]
    payload["document_form_bootstrap"]["servicios"] = line_item_payloads["servicios_json"]
    payload["document_form_bootstrap"]["otros_servicios"] = line_item_payloads["otros_json"]

    if getattr(source_document, "cliente", None):
        payload["clientes_prefetch"] = [
            {
                "id": source_document.cliente.id,
                "nombre": str(source_document.cliente),
            }
        ]
    if getattr(source_document, "vehiculo", None):
        vehiculo = source_document.vehiculo
        payload["vehiculos_prefetch"] = [
            {
                "id": vehiculo.id,
                "cliente_id": getattr(vehiculo, "cliente_id", None),
                "label": _vehicle_form_label(vehiculo),
                "text": _vehicle_form_label(vehiculo),
                "display_label": _vehicle_form_label(vehiculo),
                "patente": vehiculo.patente or "",
                "placa": vehiculo.patente or "",
                "vin": vehiculo.vin or "",
                "anio": vehiculo.anio,
                "marca": vehiculo.get_marca_display(),
                "modelo": vehiculo.get_modelo_display(),
            }
        ]

    return payload


def build_line_item_payloads(*, mode, request=None, source_document=None, source_draft=None):
    if request is not None and getattr(request, "method", "GET").upper() == "POST":
        return {
            "repuestos_json": _safe_json_list(request.POST.get("repuestos_json")),
            "servicios_json": _safe_json_list(request.POST.get("servicios_json")),
            "otros_json": _safe_json_list(request.POST.get("otros_json")),
        }

    # Prefill desde sesión de desarme
    if request is not None:
        session_prefill = request.session.get("desarme_repuestos_prefill")
        if session_prefill:
            return {
                "repuestos_json": session_prefill,
                "servicios_json": [],
                "otros_json": [],
            }

    if getattr(mode, "is_clean", False):
        return _empty_line_item_payloads()

    if source_document is None:
        source_document = getattr(mode, "source_document", None)
    if source_document is not None:
        return serialize_document_line_items(source_document)

    if source_draft is not None:
        return serialize_draft_line_items(source_draft)

    return _empty_line_item_payloads()


def build_prefetch_payloads(*, empresa, language, mode, country_code=None):
    if not empresa or getattr(mode, "is_clean", False):
        return _blank_prefetch()

    from decimal import Decimal

    from taller.models.clientes import Cliente
    from taller.models.repuesto import Repuesto
    from taller.models.vehiculos import Vehiculo
    from taller.servicios.catalog_bootstrap import (
        ensure_company_services_catalog,
        get_master_catalog_service_items,
    )
    from taller.servicios.models import Servicio, ServicioExterno

    country_code = str(country_code or getattr(empresa, "pais", None) or "CL").upper()
    ensure_company_services_catalog(empresa, country_code)

    payload = _blank_prefetch()
    payload["clientes_prefetch"] = [
        {
            "id": cliente.id,
            "nombre": str(cliente),
            "nombre_completo": str(cliente),
            "email": cliente.email or "",
            "telefono": cliente.telefono or "",
        }
        for cliente in Cliente.objects.filter(empresa=empresa)
        .order_by("nombre", "apellido")
        .only("id", "nombre", "apellido", "email", "telefono")[:50]
    ]
    payload["vehiculos_prefetch"] = [
        {
            "id": vehiculo.id,
            "cliente_id": vehiculo.cliente_id,
            "label": _vehicle_form_label(vehiculo),
            "text": _vehicle_form_label(vehiculo),
            "display_label": _vehicle_form_label(vehiculo),
            "patente": vehiculo.patente or "",
            "placa": vehiculo.patente or "",
            "vin": vehiculo.vin or "",
            "anio": vehiculo.anio,
            "marca": vehiculo.get_marca_display(),
            "modelo": vehiculo.get_modelo_display(),
        }
        for vehiculo in Vehiculo.objects.filter(
            empresa=empresa,
            tipo_uso=Vehiculo.TIPO_USO_CLIENTE,
            cliente_id__isnull=False,
        )
        .select_related("marca", "modelo")
        .order_by("-id")[:100]
    ]
    payload["repuestos_prefetch"] = [
        {
            "id": repuesto.id,
            "codigo": repuesto.part_number or "",
            "nombre": repuesto.nombre,
            "proveedor": repuesto.proveedor or "",
            "precio_compra": float(repuesto.precio_compra or Decimal("0")),
            "precio_venta": float(repuesto.precio_venta or Decimal("0")),
            "precio_venta_sugerido": float(repuesto.precio_venta or Decimal("0")),
            "stock": int(repuesto.cantidad_stock or 0),
            "stock_minimo": int(repuesto.stock_minimo or 0),
        }
        for repuesto in Repuesto.objects.filter(empresa=empresa)
        .order_by("nombre")
        .only(
            "id",
            "part_number",
            "nombre",
            "proveedor",
            "precio_compra",
            "precio_venta",
            "cantidad_stock",
            "stock_minimo",
        )[:50]
    ]

    servicios_qs = (
        Servicio.objects.filter(
            empresa=empresa,
            categoria__country=country_code,
            names__language=language,
        )
        .select_related("categoria", "subcategoria")
        .prefetch_related("names", "categoria__names", "subcategoria__names")
        .distinct()
    )
    payload["servicios_prefetch"] = [
        {
            "id": servicio.id,
            "nombre": servicio.get_label(language),
            "codigo_interno": servicio.codigo_interno or "",
            "categoria": servicio.categoria.get_label(language) if servicio.categoria else "",
            "categoria_code": servicio.categoria.code if servicio.categoria else "",
            "subcategoria": (
                servicio.subcategoria.get_label(language) if servicio.subcategoria else ""
            ),
            "subcategoria_code": servicio.subcategoria.code if servicio.subcategoria else "",
            "label": servicio.get_label(language),
            "text": servicio.get_label(language),
            "precio": float(servicio.precio_base or Decimal("0")),
            "precio_base": float(servicio.precio_base or Decimal("0")),
            "precio_sugerido": float(servicio.precio_base or Decimal("0")),
            "precio_cliente": float(servicio.precio_base or Decimal("0")),
        }
        for servicio in servicios_qs[:50]
    ]
    if not payload["servicios_prefetch"]:
        payload["servicios_prefetch"] = get_master_catalog_service_items(
            country_code,
            language=language,
            limit=50,
        )
    payload["otros_servicios_prefetch"] = [
        {
            "id": servicio.id,
            "nombre": servicio.nombre,
            "empresa": servicio.empresa_externa,
            "empresa_ext": servicio.empresa_externa,
            "empresa_externa": servicio.empresa_externa,
            "categoria": servicio.categoria.get_label(language) if servicio.categoria else "",
            "subcategoria": (
                servicio.subcategoria.get_label(language) if servicio.subcategoria else ""
            ),
            "precio_taller": float(servicio.costo_taller or Decimal("0")),
            "costo_taller": float(servicio.costo_taller or Decimal("0")),
            "precio": float(servicio.precio_cliente or Decimal("0")),
            "precio_cliente": float(servicio.precio_cliente or Decimal("0")),
            "label": servicio.nombre,
            "text": servicio.nombre,
        }
        for servicio in ServicioExterno.objects.filter(
            empresa=empresa,
            activo=True,
            categoria__country=country_code,
        )
        .select_related("categoria", "subcategoria")
        .prefetch_related("categoria__names", "subcategoria__names")[:50]
    ]
    return payload


def build_form_bootstrap(*, form_mode, cliente, vehiculo_id, line_item_payloads):
    return {
        "mode": _mode_value(form_mode),
        "cliente": cliente,
        "vehiculo_id": str(vehiculo_id or ""),
        "line_items": {
            "repuestos": line_item_payloads.get("repuestos_json", []),
            "servicios": line_item_payloads.get("servicios_json", []),
            "otros": line_item_payloads.get("otros_json", []),
        },
        "has_server_line_items": has_server_line_items(line_item_payloads),
    }


def has_server_line_items(target=None, *args, **kwargs):
    if isinstance(target, dict):
        return any(target.get(key) for key in ("repuestos_json", "servicios_json", "otros_json"))

    if target is None:
        return False

    try:
        return any(
            getattr(target, relation).exists()
            for relation in ("lineas_repuesto", "lineas_servicio", "lineas_otro_servicio")
        )
    except Exception:
        return False
