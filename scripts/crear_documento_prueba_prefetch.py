#!/usr/bin/env python3
"""
Script para crear un documento de prueba con líneas y verificar
que las vistas funcionan correctamente con prefetch_related
"""

import os
import sys

import django

# Configurar Django
sys.path.append(".")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
django.setup()


from taller.models.clientes import Cliente
from taller.models.documento import Documento
from taller.models.empresa import Empresa
from taller.models.lineas_documento import (
    LineaOtroServicio,
    LineaRepuesto,
    LineaServicio,
)


def crear_documento_prueba():
    """Crear un documento de prueba con líneas para verificar las vistas"""
    print("🧪 CREANDO DOCUMENTO DE PRUEBA CON LÍNEAS")
    print("=" * 60)

    # Buscar una empresa existente
    empresa = Empresa.objects.first()
    if not empresa:
        print("❌ No se encontraron empresas")
        return None

    print(f"📢 Usando empresa: {empresa.nombre_taller}")

    # Buscar un cliente existente o crear uno simple
    cliente = Cliente.objects.filter(empresa=empresa).first()
    if not cliente:
        cliente = Cliente.objects.create(
            empresa=empresa,
            nombre="Cliente Prueba",
            telefono="123456789",
            email="prueba@test.com",
        )
        print(f"📝 Cliente creado: {cliente.nombre}")
    else:
        print(f"👤 Cliente existente: {cliente.nombre}")

    # Crear documento
    documento = Documento.objects.create(
        empresa=empresa,
        tipo="PRES",
        numero=999999,  # Número único para identificar fácilmente
        cliente=cliente,
        estado="DRAFT",
    )
    print(f"📄 Documento creado: {documento.numero_documento}")

    # Crear líneas de repuesto
    linea_rep1 = LineaRepuesto.objects.create(
        documento=documento,
        codigo="REP001",
        nombre="Filtro de Aceite Prueba",
        cantidad=2,
        precio_unitario=15000,
        descuento=10,
    )
    print(
        f"🔧 Repuesto 1: {linea_rep1.nombre} - ${linea_rep1.precio_unitario} x {linea_rep1.cantidad}"
    )

    linea_rep2 = LineaRepuesto.objects.create(
        documento=documento,
        codigo="REP002",
        nombre="Pastillas de Freno Prueba",
        cantidad=1,
        precio_unitario=45000,
        descuento=5,
    )
    print(
        f"🔧 Repuesto 2: {linea_rep2.nombre} - ${linea_rep2.precio_unitario} x {linea_rep2.cantidad}"
    )

    # Crear líneas de servicio (necesitamos un servicio del catálogo)
    from taller.servicios.models import Servicio

    servicio = Servicio.objects.filter(country=empresa.pais).first()
    if servicio:
        linea_serv1 = LineaServicio.objects.create(
            documento=documento,
            servicio=servicio,
            codigo="SERV001",
            nombre="Cambio de Aceite Prueba",
            cantidad=1,
            precio_unitario=25000,
            descuento=0,
        )
        print(f"🛠️  Servicio 1: {linea_serv1.nombre} - ${linea_serv1.precio_unitario}")
    else:
        print("⚠️  No hay servicios en el catálogo para crear línea de servicio")

    # Crear línea de otro servicio
    linea_otro1 = LineaOtroServicio.objects.create(
        documento=documento,
        nombre="Alineación Externa Prueba",
        empresa_externa="Taller Externo ABC",
        cantidad=1,
        costo_interno=20000,
        precio_cliente=30000,
    )
    print(f"🏢 Otro servicio: {linea_otro1.nombre} - ${linea_otro1.precio_cliente}")

    return documento


def probar_vista_ver_documento(documento):
    """Simular la vista ver_documento con prefetch_related"""
    print("\n🔍 PROBANDO VISTA VER_DOCUMENTO")
    print("=" * 40)

    # Simular la consulta de la vista optimizada
    documento_optimizado = (
        Documento.objects.select_related("cliente", "vehiculo", "mecanico")
        .prefetch_related("lineas_repuesto", "lineas_servicio", "lineas_otro_servicio")
        .get(id=documento.id)
    )

    # Obtener líneas usando prefetch
    repuestos = documento_optimizado.lineas_repuesto.all()
    servicios = documento_optimizado.lineas_servicio.all()
    otros_servicios = documento_optimizado.lineas_otro_servicio.all()

    print(f"📦 Repuestos encontrados: {repuestos.count()}")
    for rep in repuestos:
        precio_rep = rep.precio_unitario
        cantidad_rep = rep.cantidad
        descuento_rep = rep.descuento
        subtotal = precio_rep * cantidad_rep * (1 - descuento_rep / 100)
        print(
            f"   - {rep.nombre}: ${precio_rep} x {cantidad_rep} (desc: {descuento_rep}%) = ${subtotal}"
        )

    print(f"🛠️  Servicios encontrados: {servicios.count()}")
    for serv in servicios:
        precio_serv = serv.precio_unitario
        descuento_serv = serv.descuento
        subtotal = precio_serv * (1 - descuento_serv / 100)
        print(f"   - {serv.nombre}: ${precio_serv} (desc: {descuento_serv}%) = ${subtotal}")

    print(f"🏢 Otros servicios encontrados: {otros_servicios.count()}")
    for otro in otros_servicios:
        precio_otro = otro.precio_cliente
        print(f"   - {otro.nombre} ({otro.empresa_externa}): ${precio_otro}")

    # Calcular totales como en la vista
    subtotal_repuestos = sum(
        rep.precio_unitario * rep.cantidad * (1 - rep.descuento / 100) for rep in repuestos
    )
    subtotal_servicios = sum(
        serv.precio_unitario * (1 - serv.descuento / 100) for serv in servicios
    )
    subtotal_otros_servicios = sum(otro.precio_cliente for otro in otros_servicios)

    subtotal = subtotal_repuestos + subtotal_servicios + subtotal_otros_servicios
    iva = subtotal * 0.19
    total = subtotal + iva

    print("\n💰 TOTALES:")
    print(f"   Subtotal repuestos: ${subtotal_repuestos:,.0f}")
    print(f"   Subtotal servicios: ${subtotal_servicios:,.0f}")
    print(f"   Subtotal otros servicios: ${subtotal_otros_servicios:,.0f}")
    print(f"   Subtotal: ${subtotal:,.0f}")
    print(f"   IVA (19%): ${iva:,.0f}")
    print(f"   TOTAL: ${total:,.0f}")

    return True


if __name__ == "__main__":
    try:
        # Crear documento de prueba
        documento = crear_documento_prueba()

        if documento:
            # Probar vista
            probar_vista_ver_documento(documento)

            print("\n✅ PRUEBA COMPLETADA EXITOSAMENTE")
            print(f"📄 Documento de prueba creado: {documento.numero_documento}")
            print(
                f"🔗 Puede probarlo en la interfaz web navegando a ver documento #{documento.numero_documento}"
            )
        else:
            print("\n❌ ERROR: No se pudo crear el documento de prueba")

    except Exception as e:
        print(f"\n❌ ERROR EN PRUEBA: {e}")
        import traceback

        traceback.print_exc()
