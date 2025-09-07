#!/usr/bin/env python
import os
import sys

import django

# Configurar Django
sys.path.append(os.path.dirname(__file__))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "egarage.settings")
django.setup()

from datetime import date
from decimal import Decimal

from taller.documentos.models import *
from taller.models import *
from taller.models.clientes import Cliente
from taller.models.vehiculos import Vehiculo

# Obtener datos
emp = Empresa.objects.get(nombre_taller="USA Test Garage")
cli = Cliente.objects.get(empresa=emp, nombre="Cliente Demo")
veh = Vehiculo.objects.filter(empresa=emp).first()
repuestos = list(Repuesto.objects.filter(empresa=emp)[:3])

print(f"Empresa: {emp}")
print(f"Cliente: {cli}")
print(f"Vehículo: {veh}")
print(f"Repuestos: {[r.nombre for r in repuestos]}")

# Crear 3 documentos
tipos = ["OT", "FAC", "PRES"]

for i, tipo in enumerate(tipos):
    doc = Documento.objects.create(
        empresa=emp,
        cliente=cli,
        vehiculo=veh,
        tipo=tipo,
        fecha_emision=date.today(),
        estado="emitido",
        country=emp.pais,
        moneda=emp.moneda,
    )

    # Agregar repuestos (2 al primer doc, 3 al segundo, 1 al tercero)
    cantidad_rep = [2, 3, 1][i]
    total = Decimal("0")

    for j in range(cantidad_rep):
        rep = repuestos[j % len(repuestos)]
        lr = LineaRepuesto.objects.create(
            documento=doc,
            repuesto=rep,
            codigo=rep.part_number,
            nombre=rep.nombre,
            cantidad=Decimal("1"),
            precio_unitario=rep.precio_venta,
            descuento=Decimal("0"),
        )
        total += lr.cantidad * lr.precio_unitario

    # Actualizar totales
    doc.neto_repuestos = total
    doc.total = total
    doc.save()

    print(
        f"✅ Documento {doc.id} ({doc.tipo}): {doc.lineas_repuesto.count()} repuestos, Total=${doc.total}"
    )

print(
    f"\n🎉 Total documentos USA Test Garage: {Documento.objects.filter(empresa=emp).count()}"
)
