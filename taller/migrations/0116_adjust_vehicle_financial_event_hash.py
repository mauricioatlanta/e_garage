from decimal import Decimal

from django.db import migrations, models
from django.db.models import Q


def normalize_number(value):
    return format(Decimal(value or 0), "f")


def normalize_text(value):
    if value is None:
        return ""
    return str(value).strip()


def compute_sale_hash(linea):
    pieza_id = getattr(linea, "pieza_desarme_id", "NO_PIEZA")
    payload = [
        "FIN_EVENT_V1",
        "VENTA",
        str(linea.id),
        str(linea.documento_id),
        str(pieza_id),
        normalize_number(getattr(linea, "cantidad", 0)),
        normalize_number(getattr(linea, "precio_unitario", 0)),
        normalize_number(getattr(linea, "descuento", 0)),
        normalize_number(getattr(linea, "subtotal", 0)),
    ]
    return "|".join(payload)


def compute_purchase_hash(event):
    payload = [
        "FIN_EVENT_V1",
        "COMPRA",
        str(getattr(event, "vehiculo_id", "NO_VEHICULO")),
        str(getattr(event, "empresa_id", "NO_EMPRESA")),
        normalize_number(getattr(event, "monto", 0)),
        normalize_text(getattr(event, "descripcion", "")),
    ]
    return "|".join(payload)


def compute_cost_hash(event):
    payload = [
        "FIN_EVENT_V1",
        "COSTO",
        str(getattr(event, "vehiculo_id", "NO_VEHICULO")),
        str(getattr(event, "empresa_id", "NO_EMPRESA")),
        normalize_number(getattr(event, "monto", 0)),
        normalize_text(getattr(event, "descripcion", "")),
    ]
    return "|".join(payload)


def regenerate_event_hashes(apps, schema_editor):
    VehicleFinancialEvent = apps.get_model("taller", "VehicleFinancialEvent")
    LineaRepuesto = apps.get_model("taller", "LineaRepuesto")

    for event in VehicleFinancialEvent.objects.filter(event_hash__isnull=True).order_by("created_at", "id"):
        if event.event_type == "VENTA":
            if not getattr(event, "linea_repuesto_id", None):
                print(f"SKIP event #{event.id} VENTA sin linea_repuesto")
                continue
            linea = LineaRepuesto.objects.filter(id=event.linea_repuesto_id).first()
            if not linea:
                print(f"SKIP event #{event.id} VENTA linea_repuesto no encontrada")
                continue
            event_hash = compute_sale_hash(linea)
        elif event.event_type == "COMPRA":
            event_hash = compute_purchase_hash(event)
        elif event.event_type == "COSTO":
            event_hash = compute_cost_hash(event)
        else:
            print(f"SKIP event #{event.id} tipo no soportado {event.event_type}")
            continue

        existing = VehicleFinancialEvent.objects.filter(event_hash=event_hash).order_by("created_at", "id").first()
        if existing:
            print(
                f"COLLISION: event #{event.id} mantiene NULL porque el hash ya existe en event #{existing.id}"
            )
            continue

        event.event_hash = event_hash
        event.save(update_fields=["event_hash"])
        print(f"FIXED: event #{event.id} assigned hash {event_hash}")


class Migration(migrations.Migration):

    dependencies = [
        ("taller", "0115_change_comprobante_to_filefield"),
    ]

    operations = [
        migrations.RemoveConstraint(
            model_name="vehiclefinancialevent",
            name="unique_vehicle_financial_event_hash",
        ),
        migrations.AddConstraint(
            model_name="vehiclefinancialevent",
            constraint=models.UniqueConstraint(
                fields=["event_hash"],
                condition=Q(event_hash__isnull=False),
                name="uniq_vehicle_financial_event_hash",
            ),
        ),
        migrations.RunPython(regenerate_event_hashes, reverse_code=migrations.RunPython.noop),
    ]
