from decimal import Decimal

from taller.models import Empresa, Repuesto


DEFAULT_REPUESTOS = [
    {"nombre": "Aceite Motor 5W30", "codigo": "MO", "precio": Decimal("15000.00")},
    {"nombre": "Aceite Sintetico 5W40", "codigo": "MO1", "precio": Decimal("22000.00")},
    {"nombre": "Filtro de Aceite", "codigo": "OF", "precio": Decimal("8000.00")},
]


def run(empresa=None):
    if empresa is None:
        empresa = Empresa.objects.order_by("id").first()

    if empresa is None:
        raise RuntimeError("No existe ninguna Empresa para asociar los repuestos.")

    created = 0
    existing = 0

    for data in DEFAULT_REPUESTOS:
        obj, was_created = Repuesto.objects.get_or_create(
            empresa=empresa,
            part_number=data["codigo"],
            defaults={
                "nombre": data["nombre"],
                "precio_compra": data["precio"],
                "precio_venta": data["precio"],
                "cantidad_stock": 10,
                "proveedor": "",
            },
        )

        if was_created:
            print(f"Creado: {obj.nombre} [{obj.part_number}]")
            created += 1
        else:
            print(f"Ya existe: {obj.nombre} [{obj.part_number}]")
            existing += 1

    print("\n--- RESUMEN ---")
    print(f"Empresa: {empresa.nombre_taller} (id={empresa.id})")
    print(f"Creados: {created}")
    print(f"Existentes: {existing}")
