"""
Script para ejecutar en Django shell para crear líneas de documento

Copiar y pegar en: python manage.py shell
"""

from decimal import Decimal

# Imports
from taller.models.documento import Documento
from taller.models.lineas_documento import LineaRepuesto, LineaServicio

# Buscar primer documento
docs = Documento.objects.all()
print(f"📄 Total documentos: {docs.count()}")

if docs.exists():
    doc = docs.first()
    print(f"🎯 Trabajando con documento: {doc.numero} ({doc.tipo})")

    # Verificar estado actual
    rep_count = doc.lineas_repuesto.count()
    serv_count = doc.lineas_servicio.count()
    print(f"📊 Estado actual - Repuestos: {rep_count}, Servicios: {serv_count}")

    # Si no tiene líneas, agregar algunas
    if rep_count == 0:
        # Crear líneas de repuesto
        r1 = LineaRepuesto.objects.create(
            documento=doc,
            codigo="REP001",
            nombre="Filtro de Aceite",
            cantidad=2,
            precio_unitario=Decimal("15000.00"),
            descuento=Decimal("0.00"),
        )

        r2 = LineaRepuesto.objects.create(
            documento=doc,
            codigo="REP002",
            nombre="Pastillas de Freno",
            cantidad=1,
            precio_unitario=Decimal("45000.00"),
            descuento=Decimal("10.00"),
        )
        print("✅ Líneas de repuesto creadas")

    if serv_count == 0:
        # Crear líneas de servicio
        s1 = LineaServicio.objects.create(
            documento=doc,
            codigo="SER001",
            nombre="Cambio de Aceite",
            cantidad=1,
            precio_unitario=Decimal("25000.00"),
            descuento=Decimal("0.00"),
        )

        s2 = LineaServicio.objects.create(
            documento=doc,
            codigo="SER002",
            nombre="Revisión General",
            cantidad=1,
            precio_unitario=Decimal("35000.00"),
            descuento=Decimal("5.00"),
        )
        print("✅ Líneas de servicio creadas")

    # Verificar totales
    print("\n📊 TOTALES CALCULADOS:")
    try:
        total_rep = doc.total_repuestos()
        total_serv = doc.total_servicios()
        total_gen = doc.total_general()

        print(f"   Repuestos: ${total_rep}")
        print(f"   Servicios: ${total_serv}")
        print(f"   Total: ${total_gen}")

        if total_rep > 0 or total_serv > 0:
            print("\n🎉 ¡ÉXITO! Los totales ahora aparecerán en la vista de lista")
        else:
            print("\n⚠️  Los totales siguen en 0 - revisar cálculos")

    except Exception as e:
        print(f"❌ Error calculando totales: {e}")

else:
    print("❌ No hay documentos en la base de datos")

print("\n✅ Script completado")
