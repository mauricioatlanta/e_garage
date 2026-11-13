from decimal import Decimal
from django.db.models import Sum, Count, Avg, F, Q
from taller.models.tire import Tire

def _qs(empresa):
    return Tire.objects.filter(empresa=empresa) if empresa else Tire.objects.none()

def reporte_compra_venta(empresa):
    qs = _qs(empresa)
    total_stock = qs.aggregate(s=Sum("cantidad_stock"))["s"] or 0
    valor_compra = sum((t.cantidad_stock * (t.precio_compra or 0) for t in qs), Decimal("0"))
    valor_venta = sum((t.cantidad_stock * (t.precio_venta or 0) for t in qs), Decimal("0"))
    utilidad_potencial = valor_venta - valor_compra
    margen = (utilidad_potencial / valor_venta * 100) if valor_venta else Decimal("0")
    por_tipo = list(qs.values("tipo").annotate(
        unidades=Sum("cantidad_stock"),
        valor_compra=Sum(F("cantidad_stock") * F("precio_compra")),
        valor_venta=Sum(F("cantidad_stock") * F("precio_venta")),
        modelos=Count("id"),
    ).order_by("-valor_venta"))
    return {
        "total_stock": total_stock,
        "valor_compra": valor_compra,
        "valor_venta": valor_venta,
        "utilidad_potencial": utilidad_potencial,
        "margen_pct": round(float(margen), 1),
        "alerta_margen": float(margen) < 20,
        "por_tipo": por_tipo,
    }

def reporte_venta_por_medida(empresa):
    # v1: rotación = stock vs precio. Cuando tengas ventas ligadas a Tire, aquí se suma venta real.
    # Por ahora la recomendación usa stock + margen, que es lo que te hace comprar de más / de menos.
    qs = _qs(empresa)
    rows = list(qs.values("ancho", "perfil", "aro").annotate(
        stock=Sum("cantidad_stock"),
        modelos=Count("id"),
        precio_compra_min=Avg("precio_compra"),
        precio_venta_avg=Avg("precio_venta"),
        marcas=Count("marca", distinct=True),
    ).order_by("-stock"))
    for r in rows:
        medida = f"{r['ancho']}/{r['perfil']} R{r['aro']}"
        r["medida"] = medida
        stock = r["stock"] or 0
        # Regla de experto vulcanización:
        if stock == 0:
            r["recomendacion"] = "COMPRAR URGENTE"
            r["clase"] = "urgente"
        elif stock <= 4:
            r["recomendacion"] = "COMPRAR"
            r["clase"] = "comprar"
        elif stock >= 20:
            r["recomendacion"] = "NO COMPRAR / LIQUIDAR"
            r["clase"] = "no-comprar"
        else:
            r["recomendacion"] = "MANTENER"
            r["clase"] = "mantener"
        r["margen_pct"] = round(float(((r["precio_venta_avg"] or 0) - (r["precio_compra_min"] or 0)) / (r["precio_venta_avg"] or 1) * 100), 1) if r["precio_venta_avg"] else 0
    return rows

def reporte_proveedores_por_medida(empresa):
    qs = _qs(empresa)
    rows = list(qs.values("proveedor", "ancho", "perfil", "aro").annotate(
        stock=Sum("cantidad_stock"),
        precio_compra_min=Avg("precio_compra"),
        precio_compra_avg=Avg("precio_compra"),
        precio_venta_avg=Avg("precio_venta"),
        modelos=Count("id"),
    ).order_by("ancho", "perfil", "aro", "precio_compra_avg"))
    # Marcar más barato / más caro por medida
    from collections import defaultdict
    por_medida = defaultdict(list)
    for r in rows:
        medida = f"{r['ancho']}/{r['perfil']} R{r['aro']}"
        r["medida"] = medida
        r["proveedor"] = r["proveedor"] or "Sin proveedor"
        r["margen"] = (r["precio_venta_avg"] or 0) - (r["precio_compra_avg"] or 0)
        r["margen_pct"] = round(float(r["margen"] / (r["precio_venta_avg"] or 1) * 100), 1) if r["precio_venta_avg"] else 0
        por_medida[medida].append(r)
    for medida, lst in por_medida.items():
        lst_sorted = sorted(lst, key=lambda x: float(x["precio_compra_avg"] or 0))
        if lst_sorted:
            lst_sorted[0]["badge"] = "MÁS BARATO - RECOMENDADO"
            lst_sorted[-1]["badge"] = "MÁS CARO" if len(lst_sorted) > 1 else ""
    return rows

def reporte_mecanicos_vulcanizacion(empresa):
    # Usa Documento + Tecnico si existen, si no devuelve lista vacía sin romper
    try:
        from taller.models.documento import Documento
        from taller.models.tecnico import Tecnico
        docs = Documento.objects.filter(empresa=empresa) if empresa else Documento.objects.none()
        # Intenta agrupar por tecnico__nombre, si el campo se llama distinto, cae al except
        rows = list(docs.values("tecnico__nombre").annotate(
            total_documentos=Count("id"),
            total=Sum("total"),
        ).order_by("-total_documentos")[:20])
        for r in rows:
            r["nombre"] = r.get("tecnico__nombre") or "Sin técnico"
        return rows
    except Exception as e:
        return [{"nombre": f"Sin datos de Documento todavía ({e})", "total_documentos": 0, "total": 0}]
