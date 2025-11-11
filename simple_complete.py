from decimal import Decimal

from taller.documentos.models import *
from taller.models import Empresa
from taller.servicios.models import Servicio, ServicioExterno

# Obtener datos
emp = Empresa.objects.get(nombre_taller="USA Test Garage")
docs = list(Documento.objects.filter(empresa=emp).order_by("id"))
servicios = list(Servicio.objects.filter(empresa=emp)[:4])
servicios_ext = list(ServicioExterno.objects.filter(empresa=emp)[:4])

print(f"Documentos: {len(docs)}")
print(f"Servicios: {len(servicios)}")
print(f"Servicios externos: {len(servicios_ext)}")

# Actualizar millas del vehículo
if docs:
    veh = docs[0].vehiculo
    veh.millas = 85000
    veh.save()
    print(f"✅ Vehículo actualizado: {veh} - Millas: {veh.millas}")

# Agregar solo servicios internos primero
for i, doc in enumerate(docs[:2]):  # Solo primeros 2 docs
    print(f"\n📄 Documento {doc.id} ({doc.tipo}):")

    # Agregar 1 servicio interno
    serv = servicios[i % len(servicios)]
    precio = Decimal("50.00") + (i * Decimal("10.00"))

    try:
        ls = LineaServicio.objects.create(
            documento=doc,
            servicio=serv,
            nombre=serv.nombre,
            cantidad=Decimal("1"),
            precio_unitario=precio,
            descuento=Decimal("0"),
        )
        print(f"  ✅ Servicio: {ls.nombre} - ${precio}")

        # Actualizar totales
        doc.neto_servicios = precio
        doc.total = doc.neto_repuestos + precio
        doc.save()
        print(f"  💰 Total actualizado: ${doc.total}")

    except Exception as e:
        print(f"  ❌ Error servicio: {e}")

# Agregar servicios externos usando nuevo método
for i, doc in enumerate(docs[2:], 2):  # Últimos 2 docs
    print(f"\n📄 Documento {doc.id} ({doc.tipo}):")

    if servicios_ext:
        serv_ext = servicios_ext[i % len(servicios_ext)]

        try:
            los = LineaOtroServicio.objects.create(
                documento=doc,
                servicio_externo=serv_ext,
                nombre=serv_ext.nombre,
                empresa_externa=serv_ext.empresa_externa,
                cantidad=Decimal("1"),
                costo_interno=serv_ext.costo_taller,
                precio_cliente=serv_ext.precio_cliente,
                descuento=Decimal("0"),
            )
            print(f"  ✅ Otro servicio: {los.nombre} - ${los.precio_cliente}")

            # Actualizar totales
            doc.neto_otros_servicios = serv_ext.precio_cliente
            doc.total = doc.neto_repuestos + serv_ext.precio_cliente
            doc.save()
            print(f"  💰 Total actualizado: ${doc.total}")

        except Exception as e:
            print(f"  ❌ Error otro servicio: {e}")

print("\n🎯 Resumen final:")
for doc in docs:
    rep_count = doc.lineas_repuesto.count() if hasattr(doc, "lineas_repuesto") else 0
    serv_count = doc.lineas_servicio.count() if hasattr(doc, "lineas_servicio") else 0
    otros_count = doc.lineas_otroservicio.count() if hasattr(doc, "lineas_otroservicio") else 0

    print(
        f"Doc {doc.id}: REP={rep_count}, SERV={serv_count}, OTROS={otros_count}, TOTAL=${doc.total}"
    )
