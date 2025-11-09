from decimal import ROUND_HALF_UP, Decimal

from django.db import migrations, models

CLP_PLACES = Decimal("1")  # 0 decimales
USD_PLACES = Decimal("0.01")  # 2 decimales


def _money_quantize(amount: Decimal, pais: str) -> Decimal:
    if amount is None:
        amount = Decimal("0")
    places = CLP_PLACES if pais == "CL" else USD_PLACES
    return Decimal(amount).quantize(places, rounding=ROUND_HALF_UP)


def backfill_lineas(apps, schema_editor):
    Documento = apps.get_model("taller", "Documento")
    LineaRepuesto = apps.get_model("taller", "LineaRepuesto")
    LineaServicio = apps.get_model("taller", "LineaServicio")
    LineaOtroServicio = apps.get_model("taller", "LineaOtroServicio")

    # --- Repuestos: subtotal = cantidad * precio_unitario - descuento (>=0)
    for lr in (
        LineaRepuesto.objects.select_related("documento__empresa").all().iterator()
    ):
        try:
            pais = getattr(getattr(lr.documento, "empresa", None), "pais", "CL")
        except Exception:
            pais = "CL"
        cantidad = Decimal(lr.cantidad or 0)
        precio = Decimal(lr.precio_unitario or 0)
        desc = Decimal(lr.descuento or 0)
        bruto = (cantidad * precio) - desc
        subtotal = _money_quantize(bruto if bruto > 0 else Decimal("0"), pais)
        LineaRepuesto.objects.filter(pk=lr.pk).update(subtotal=subtotal)

    # --- Servicios: subtotal = cantidad * precio_unitario - descuento (>=0)
    for ls in (
        LineaServicio.objects.select_related("documento__empresa").all().iterator()
    ):
        try:
            pais = getattr(getattr(ls.documento, "empresa", None), "pais", "CL")
        except Exception:
            pais = "CL"
        cantidad = Decimal(ls.cantidad or 0)
        precio = Decimal(ls.precio_unitario or 0)
        desc = Decimal(ls.descuento or 0)
        bruto = (cantidad * precio) - desc
        subtotal = _money_quantize(bruto if bruto > 0 else Decimal("0"), pais)
        LineaServicio.objects.filter(pk=ls.pk).update(subtotal=subtotal)

    # --- Otros/Externos:
    # subtotal = precio_cliente * cantidad
    # ganancia = (precio_cliente - costo_interno) * cantidad
    for lo in (
        LineaOtroServicio.objects.select_related("documento__empresa").all().iterator()
    ):
        try:
            pais = getattr(getattr(lo.documento, "empresa", None), "pais", "CL")
        except Exception:
            pais = "CL"
        cantidad = Decimal(lo.cantidad or 0)
        costo = Decimal(lo.costo_interno or 0)
        precio_cli = Decimal(lo.precio_cliente or 0)
        subtotal = _money_quantize(cantidad * precio_cli, pais)
        ganancia = _money_quantize((precio_cli - costo) * cantidad, pais)
        LineaOtroServicio.objects.filter(pk=lo.pk).update(
            subtotal=subtotal, ganancia=ganancia
        )

    # Opcional: recalcular totales del documento si existe el método en el modelo vivo
    try:
        from taller.models import Documento as LiveDocumento  # noqa

        use_live = hasattr(LiveDocumento, "recalcular_totales")
    except Exception:
        use_live = False

    if use_live:
        # Recorre documentos y recalcula
        for d in Documento.objects.all().iterator():
            try:
                ld = LiveDocumento.objects.get(pk=d.pk)
                ld.recalcular_totales(save=True)
            except Exception:
                pass


def noop_reverse(apps, schema_editor):
    # No deshacemos datos en reverse
    pass


class Migration(migrations.Migration):
    dependencies = [
        ("taller", "0017_auto_20251006_1931"),
    ]

    operations = [
        # ---------- Repuesto ----------
        migrations.AddField(
            model_name="linearepuesto",
            name="subtotal",
            field=models.DecimalField(default=0, max_digits=14, decimal_places=2),
        ),
        migrations.AlterField(
            model_name="linearepuesto",
            name="cantidad",
            field=models.DecimalField(default=1, max_digits=10, decimal_places=2),
        ),
        migrations.AlterField(
            model_name="linearepuesto",
            name="precio_unitario",
            field=models.DecimalField(default=0, max_digits=12, decimal_places=2),
        ),
        migrations.AlterField(
            model_name="linearepuesto",
            name="descuento",
            field=models.DecimalField(default=0, max_digits=12, decimal_places=2),
        ),
        migrations.AddIndex(
            model_name="linearepuesto",
            index=models.Index(fields=["documento"], name="idx_lr_doc"),
        ),
        # ---------- Servicio ----------
        migrations.AddField(
            model_name="lineaservicio",
            name="subtotal",
            field=models.DecimalField(default=0, max_digits=14, decimal_places=2),
        ),
        migrations.AlterField(
            model_name="lineaservicio",
            name="cantidad",
            field=models.DecimalField(default=1, max_digits=10, decimal_places=2),
        ),
        migrations.AlterField(
            model_name="lineaservicio",
            name="precio_unitario",
            field=models.DecimalField(default=0, max_digits=12, decimal_places=2),
        ),
        migrations.AlterField(
            model_name="lineaservicio",
            name="descuento",
            field=models.DecimalField(default=0, max_digits=12, decimal_places=2),
        ),
        migrations.AddIndex(
            model_name="lineaservicio",
            index=models.Index(fields=["documento"], name="idx_ls_doc"),
        ),
        # ---------- Otros/Externos ----------
        migrations.AddField(
            model_name="lineaotroservicio",
            name="ganancia",
            field=models.DecimalField(default=0, max_digits=14, decimal_places=2),
        ),
        migrations.AddField(
            model_name="lineaotroservicio",
            name="subtotal",
            field=models.DecimalField(default=0, max_digits=14, decimal_places=2),
        ),
        migrations.AlterField(
            model_name="lineaotroservicio",
            name="cantidad",
            field=models.DecimalField(default=1, max_digits=10, decimal_places=2),
        ),
        migrations.AlterField(
            model_name="lineaotroservicio",
            name="costo_interno",
            field=models.DecimalField(default=0, max_digits=12, decimal_places=2),
        ),
        migrations.AlterField(
            model_name="lineaotroservicio",
            name="precio_cliente",
            field=models.DecimalField(default=0, max_digits=12, decimal_places=2),
        ),
        migrations.AddIndex(
            model_name="lineaotroservicio",
            index=models.Index(fields=["documento"], name="idx_los_doc"),
        ),
        # ---------- Backfill ----------
        migrations.RunPython(backfill_lineas, reverse_code=noop_reverse),
    ]
