#!/usr/bin/env python
"""
Script para generar documentos de prueba para la cuenta "mauricio1"
- 10 documentos de cada tipo (Orden de trabajo, Presupuesto, Factura)
- Usar clientes y vehículos existentes de esta empresa
"""

import os
import random
import sys
from datetime import datetime, timedelta
from decimal import Decimal

import django

# Configurar Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gestion_taller.settings")
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
django.setup()

from django.contrib.auth.models import User

from taller.models.clientes import Cliente
from taller.models.documento import Documento
from taller.models.empresa import Empresa
from taller.models.lineas_documento import (LineaOtroServicio, LineaRepuesto,
                                            LineaServicio)
from taller.models.repuesto import Repuesto
from taller.models.tecnico import Tecnico
from taller.models.tienda import Tienda
from taller.models.vehiculos import Vehiculo
from taller.servicios.models import Servicio


def crear_documentos_mauricio1():
    print("🚀 Creando documentos para cuenta mauricio1...")

    # Obtener usuario mauricio1
    try:
        usuario = User.objects.get(username="mauricio1")
        print(f"✅ Usuario encontrado: {usuario.username}")
    except User.DoesNotExist:
        print("❌ Usuario mauricio1 no encontrado")
        return

    # Obtener empresa de mauricio1
    try:
        empresa = Empresa.objects.get(user=usuario)
        print(f"✅ Empresa: {empresa.nombre_taller}")
    except Empresa.DoesNotExist:
        print("❌ Empresa no encontrada para mauricio1")
        return

    # Obtener clientes existentes de esta empresa
    clientes = list(Cliente.objects.filter(empresa=empresa))
    print(f"✅ Clientes encontrados: {len(clientes)}")

    if not clientes:
        print("❌ No hay clientes para esta empresa")
        return

    # Obtener vehículos existentes
    vehiculos = list(Vehiculo.objects.filter(empresa=empresa))
    print(f"✅ Vehículos encontrados: {len(vehiculos)}")

    if not vehiculos:
        print("❌ No hay vehículos para esta empresa")
        return

    # Obtener técnicos existentes
    tecnicos = list(Tecnico.objects.filter(empresa=empresa))
    print(f"✅ Técnicos encontrados: {len(tecnicos)}")

    if not tecnicos:
        print("❌ No hay técnicos. Creando técnico por defecto...")
        tecnico_default = Tecnico.objects.create(
            nombre="Técnico Principal",
            empresa=empresa,
            telefono="+56912345678",
            direccion="Dirección principal",
            activo=True,
        )
        tecnicos = [tecnico_default]

    # Obtener repuestos existentes
    repuestos = list(Repuesto.objects.filter(empresa=empresa))
    print(f"✅ Repuestos encontrados: {len(repuestos)}")

    # Obtener servicios existentes
    servicios = list(Servicio.objects.filter(activo=True)[:15])
    print(f"✅ Servicios disponibles: {len(servicios)}")

    # Tipos de documentos
    tipos_documento = ["Presupuesto", "Orden de trabajo", "Factura"]

    documentos_creados = 0

    # Crear 10 documentos de cada tipo
    for tipo in tipos_documento:
        print(f"\n📋 Creando 10 documentos tipo: {tipo}")

        for i in range(10):
            try:
                # Seleccionar cliente y vehículo relacionado correctamente
                cliente = random.choice(clientes)

                # Buscar vehículos que pertenezcan específicamente a este cliente
                vehiculos_cliente = [v for v in vehiculos if v.cliente == cliente]

                if not vehiculos_cliente:
                    # Si no hay vehículos para este cliente, usar cualquier vehículo
                    # pero actualizar su cliente para que coincida
                    vehiculo = random.choice(vehiculos)
                    vehiculo.cliente = cliente
                    vehiculo.save()
                    print(
                        f"    📝 Vehículo {vehiculo.patente} asignado a cliente {cliente.nombre}"
                    )
                else:
                    vehiculo = random.choice(vehiculos_cliente)

                tecnico = random.choice(tecnicos)

                # Crear documento
                documento = Documento.objects.create(
                    empresa=empresa,
                    tipo_documento=tipo,
                    numero_documento=f"{tipo[:3].upper()}-{random.randint(10000, 99999)}",
                    cliente=cliente,
                    vehiculo=vehiculo,
                    tecnico=tecnico,
                    kilometraje=random.randint(5000, 200000),
                    observaciones=f"Documento de prueba {tipo} #{i+1}. Cliente: {cliente.nombre} {cliente.apellido or ''}. Vehículo: {vehiculo.marca.nombre if vehiculo.marca else 'N/A'} {vehiculo.modelo.nombre if vehiculo.modelo else 'N/A'}.",
                    tax_rate_applied=(
                        Decimal("19.00")
                        if random.choice([True, False])
                        else Decimal("0.00")
                    ),
                    fecha=datetime.now().date() - timedelta(days=random.randint(0, 30)),
                )

                # Agregar repuestos si existen
                if repuestos:
                    num_repuestos = random.randint(1, min(3, len(repuestos)))
                    repuestos_elegidos = random.sample(repuestos, num_repuestos)
                    for repuesto in repuestos_elegidos:
                        cantidad = random.randint(1, 3)
                        precio = max(
                            1000, repuesto.precio_venta + random.randint(-3000, 10000)
                        )

                        LineaRepuesto.objects.create(
                            documento=documento,
                            repuesto=repuesto,
                            cantidad=cantidad,
                            precio_unitario=precio,
                            codigo=repuesto.part_number,
                            nombre=repuesto.nombre_repuesto,
                        )

                # Agregar servicios si existen
                if servicios:
                    num_servicios = random.randint(1, min(3, len(servicios)))
                    servicios_elegidos = random.sample(servicios, num_servicios)
                    for servicio in servicios_elegidos:
                        precio_base = servicio.precio_base or 25000
                        precio = max(
                            5000, int(precio_base) + random.randint(-5000, 15000)
                        )

                        LineaServicio.objects.create(
                            documento=documento,
                            nombre=servicio.get_label(),
                            precio_unitario=precio,
                        )

                # Agregar otros servicios ocasionalmente
                if servicios and random.choice([True, False]):
                    servicio_base = random.choice(servicios)
                    precio_cliente = random.randint(25000, 60000)
                    costo_interno = random.randint(15000, 40000)

                    LineaOtroServicio.objects.create(
                        documento=documento,
                        servicio=servicio_base,
                        nombre=f"Servicio externo - {servicio_base.get_label()}",
                        empresa_externa=random.choice(
                            [
                                "Servicios Externos SA",
                                "Taller Especializado",
                                "Proveedores Unidos",
                            ]
                        ),
                        costo_interno=costo_interno,
                        precio_cliente=precio_cliente,
                        observaciones=f"Servicio subcontratado para {tipo}",
                    )

                documentos_creados += 1
                print(
                    f"  ✅ Documento {i+1}/10 - {documento.numero_documento} (PK: {documento.pk})"
                )

            except Exception as e:
                print(f"  ❌ Error creando documento {i+1}: {e}")

    print(f"\n🎉 ¡Proceso completado!")
    print(f"📊 Documentos creados para mauricio1: {documentos_creados}")

    # Estadísticas finales
    print(f"\n📋 Documentos por tipo en empresa '{empresa.nombre_taller}':")
    for tipo in tipos_documento:
        count = Documento.objects.filter(tipo_documento=tipo, empresa=empresa).count()
        print(f"  - {tipo}: {count}")

    print(f"\n📊 Totales para empresa '{empresa.nombre_taller}':")
    print(f"  - Total documentos: {Documento.objects.filter(empresa=empresa).count()}")
    print(
        f"  - Total repuestos en docs: {LineaRepuesto.objects.filter(documento__empresa=empresa).count()}"
    )
    print(
        f"  - Total servicios en docs: {LineaServicio.objects.filter(documento__empresa=empresa).count()}"
    )
    print(
        f"  - Total otros servicios: {LineaOtroServicio.objects.filter(documento__empresa=empresa).count()}"
    )


if __name__ == "__main__":
    crear_documentos_mauricio1()
