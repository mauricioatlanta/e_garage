from datetime import date
from decimal import Decimal

from taller.documentos.models import *
from taller.models import *
from taller.models.clientes import Cliente
from taller.models.vehiculos import Vehiculo

# Crear documentos simples
emp = Empresa.objects.get(nombre_taller="USA Test Garage")
cli = Cliente.objects.get(empresa=emp, nombre="Cliente Demo")
veh = Vehiculo.objects.filter(empresa=emp).first()
repuestos = list(Repuesto.objects.filter(empresa=emp)[:3])

print(f"Empresa: {emp}")
print(f"Cliente: {cli}")
print(f"Vehiculo: {veh}")
print(f"Repuestos: {len(repuestos)}")

# Documento 1: OT con 2 repuestos
doc1 = Documento.objects.create(
    empresa=emp,
    cliente=cli,
    vehiculo=veh,
    tipo="OT",
    fecha_emision=date.today(),
    estado="emitido",
    country=emp.pais,
    moneda=emp.moneda,
)
total1 = Decimal("0")
for i in range(2):
    rep = repuestos[i]
    lr = LineaRepuesto.objects.create(
        documento=doc1,
        repuesto=rep,
        codigo=rep.part_number,
        nombre=rep.nombre,
        cantidad=Decimal("1"),
        precio_unitario=rep.precio_venta,
        descuento=Decimal("0"),
    )
    total1 += lr.precio_unitario
doc1.neto_repuestos = total1
doc1.total = total1
doc1.save()
print(
    f"Doc1: {doc1.id} - {doc1.tipo} - {doc1.lineas_repuesto.count()} rep - ${doc1.total}"
)

# Documento 2: FAC con 3 repuestos
doc2 = Documento.objects.create(
    empresa=emp,
    cliente=cli,
    vehiculo=veh,
    tipo="FAC",
    fecha_emision=date.today(),
    estado="emitido",
    country=emp.pais,
    moneda=emp.moneda,
)
total2 = Decimal("0")
for rep in repuestos:
    lr = LineaRepuesto.objects.create(
        documento=doc2,
        repuesto=rep,
        codigo=rep.part_number,
        nombre=rep.nombre,
        cantidad=Decimal("1"),
        precio_unitario=rep.precio_venta,
        descuento=Decimal("0"),
    )
    total2 += lr.precio_unitario
doc2.neto_repuestos = total2
doc2.total = total2
doc2.save()
print(
    f"Doc2: {doc2.id} - {doc2.tipo} - {doc2.lineas_repuesto.count()} rep - ${doc2.total}"
)

# Documento 3: PRES con 1 repuesto
doc3 = Documento.objects.create(
    empresa=emp,
    cliente=cli,
    vehiculo=veh,
    tipo="PRES",
    fecha_emision=date.today(),
    estado="emitido",
    country=emp.pais,
    moneda=emp.moneda,
)
rep = repuestos[0]
lr = LineaRepuesto.objects.create(
    documento=doc3,
    repuesto=rep,
    codigo=rep.part_number,
    nombre=rep.nombre,
    cantidad=Decimal("1"),
    precio_unitario=rep.precio_venta,
    descuento=Decimal("0"),
)
doc3.neto_repuestos = rep.precio_venta
doc3.total = rep.precio_venta
doc3.save()
print(
    f"Doc3: {doc3.id} - {doc3.tipo} - {doc3.lineas_repuesto.count()} rep - ${doc3.total}"
)

print(f"Total documentos: {Documento.objects.filter(empresa=emp).count()}")
