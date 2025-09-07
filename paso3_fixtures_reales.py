#!/usr/bin/env python
"""
🎯 PASO 3: FIXTURES REALES PARA CL/US CON DATOS DEMO
Creación de datos realistas, coherentes y variados para pruebas funcionales
"""
import os
import sys

import django

# Configurar Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gestion_taller.settings")
django.setup()

import random
from datetime import datetime, timedelta
from decimal import Decimal

from django.contrib.auth.models import User

from taller.models import *
from taller.models.extras_vehiculo import (CajaVehiculo, ColorVehiculo,
                                           MotorVehiculo)
from taller.models.marca import Marca
from taller.models.modelo import Modelo
from taller.models.region_ciudad import TallerCiudad, TallerRegion
from taller.servicios.models import *


class FixturesRealesGenerator:
    """Generador de fixtures realistas para CL y US"""

    def __init__(self):
        self.datos_creados = {
            "usuarios": [],
            "empresas": [],
            "clientes": [],
            "vehiculos": [],
            "servicios": [],
            "documentos": [],
        }

    def limpiar_datos_demo_anteriores(self):
        """Limpiar datos demo anteriores para evitar conflictos"""
        print("🧹 LIMPIANDO DATOS DEMO ANTERIORES")
        print("-" * 50)

        # Eliminar usuarios demo
        usuarios_demo = User.objects.filter(username__contains="demo_")
        print(f"   Eliminando {usuarios_demo.count()} usuarios demo...")
        usuarios_demo.delete()

        # Eliminar servicios demo
        servicios_demo = Servicio.objects.filter(code__contains="demo_")
        print(f"   Eliminando {servicios_demo.count()} servicios demo...")
        servicios_demo.delete()

        print("   ✅ Limpieza completada\n")

    def crear_empresas_demo_chile(self):
        """Crear empresas demo realistas para Chile"""
        print("🇨🇱 CREANDO EMPRESAS DEMO CHILE")
        print("-" * 50)

        empresas_cl = [
            {
                "username": "demo_taller_santiago",
                "email": "contacto@tallerperez.cl",
                "nombre_taller": "Taller Pérez & Asociados",
                "empresa": "Servicios Automotrices Pérez Ltda.",
                "direccion": "Av. Los Leones 1234, Las Condes, Santiago",
                "telefono": "+56 2 2345 6789",
                "email_empresa": "info@tallerperez.cl",
            },
            {
                "username": "demo_mecanica_valparaiso",
                "email": "contacto@mecanicaporteña.cl",
                "nombre_taller": "Mecánica Porteña",
                "empresa": "Talleres del Puerto SpA",
                "direccion": "Av. Argentina 567, Valparaíso",
                "telefono": "+56 32 298 7654",
                "email_empresa": "servicios@mecanicaporteña.cl",
            },
            {
                "username": "demo_automotriz_concepcion",
                "email": "gerencia@autosur.cl",
                "nombre_taller": "AutoSur Concepción",
                "empresa": "Automotriz del Sur Ltda.",
                "direccion": "Av. Paicaví 890, Concepción",
                "telefono": "+56 41 234 5678",
                "email_empresa": "ventas@autosur.cl",
            },
        ]

        for datos in empresas_cl:
            # Crear usuario
            user = User.objects.create_user(
                username=datos["username"],
                email=datos["email"],
                password="demo2025",
                first_name=datos["nombre_taller"].split()[1],
                last_name="Demo",
            )

            # Crear empresa
            empresa = Empresa.objects.create(
                user=user,
                nombre_taller=datos["nombre_taller"],
                empresa=datos["empresa"],
                pais="CL",
                direccion=datos["direccion"],
                telefono=datos["telefono"],
                email=datos["email_empresa"],
                plan="premium",
                suscripcion_activa=True,
                fecha_fin=datetime.now() + timedelta(days=365),
            )

            self.datos_creados["usuarios"].append(user)
            self.datos_creados["empresas"].append(empresa)

            print(f"   ✅ {empresa.nombre_taller} creado")

        print(f"   📊 Total empresas CL: {len(empresas_cl)}\n")

    def crear_empresas_demo_usa(self):
        """Crear empresas demo realistas para USA"""
        print("🇺🇸 CREANDO EMPRESAS DEMO USA")
        print("-" * 50)

        empresas_us = [
            {
                "username": "demo_mikes_auto_miami",
                "email": "mike@mikesauto.com",
                "nombre_taller": "Mike's Auto Repair",
                "empresa": "Mike Johnson Automotive LLC",
                "direccion": "1234 Biscayne Blvd, Miami, FL 33132",
                "telefono": "+1 305 555 0123",
                "email_empresa": "service@mikesauto.com",
            },
            {
                "username": "demo_pacific_motors_la",
                "email": "info@pacificmotors.com",
                "nombre_taller": "Pacific Motors",
                "empresa": "Pacific Automotive Group Inc.",
                "direccion": "5678 Sunset Blvd, Los Angeles, CA 90028",
                "telefono": "+1 323 555 0456",
                "email_empresa": "contact@pacificmotors.com",
            },
            {
                "username": "demo_texas_automotive_dallas",
                "email": "service@texasauto.com",
                "nombre_taller": "Texas Automotive Center",
                "empresa": "Lone Star Auto Services LLC",
                "direccion": "9012 Commerce St, Dallas, TX 75201",
                "telefono": "+1 214 555 0789",
                "email_empresa": "info@texasauto.com",
            },
        ]

        for datos in empresas_us:
            # Crear usuario
            user = User.objects.create_user(
                username=datos["username"],
                email=datos["email"],
                password="demo2025",
                first_name=datos["nombre_taller"].split()[0],
                last_name="Demo",
            )

            # Crear empresa
            empresa = Empresa.objects.create(
                user=user,
                nombre_taller=datos["nombre_taller"],
                empresa=datos["empresa"],
                pais="US",
                direccion=datos["direccion"],
                telefono=datos["telefono"],
                email=datos["email_empresa"],
                plan="premium",
                suscripcion_activa=True,
                fecha_fin=datetime.now() + timedelta(days=365),
                zona_horaria="America/New_York",
            )

            self.datos_creados["usuarios"].append(user)
            self.datos_creados["empresas"].append(empresa)

            print(f"   ✅ {empresa.nombre_taller} creado")

        print(f"   📊 Total empresas US: {len(empresas_us)}\n")

    def crear_servicios_caracteristicos_chile(self):
        """Crear servicios característicos de Chile"""
        print("🔧 CREANDO SERVICIOS CARACTERÍSTICOS CHILE")
        print("-" * 50)

        # Categorías típicas Chile
        categorias_cl = [
            {
                "code": "demo_mantencion_cl",
                "nombre_es": "Mantención Preventiva",
                "nombre_en": "Preventive Maintenance",
            },
            {
                "code": "demo_reparacion_cl",
                "nombre_es": "Reparaciones Generales",
                "nombre_en": "General Repairs",
            },
            {
                "code": "demo_revision_cl",
                "nombre_es": "Revisión Técnica",
                "nombre_en": "Technical Inspection",
            },
            {
                "code": "demo_emergencia_cl",
                "nombre_es": "Servicios de Emergencia",
                "nombre_en": "Emergency Services",
            },
        ]

        for cat_data in categorias_cl:
            categoria = CategoriaServicio.objects.create(
                country="CL", code=cat_data["code"]
            )

            # Nombres en español
            CategoriaServicioName.objects.create(
                categoria=categoria,
                language="es",
                label=cat_data["nombre_es"],
                is_default=True,
            )

            # Nombres en inglés
            CategoriaServicioName.objects.create(
                categoria=categoria,
                language="en",
                label=cat_data["nombre_en"],
                is_default=True,
            )

            print(f"   ✅ Categoría: {cat_data['nombre_es']}")

        # Servicios específicos de Chile
        servicios_cl = [
            # Mantención
            {
                "cat": "demo_mantencion_cl",
                "code": "demo_cambio_aceite_cl",
                "tipo": "interno",
                "nombre_es": "Cambio de aceite y filtros",
                "nombre_en": "Oil and filter change",
                "precio": 25000,
                "aliases_es": ["cambio aceite", "mantención básica"],
                "aliases_en": ["oil change", "basic maintenance"],
            },
            {
                "cat": "demo_mantencion_cl",
                "code": "demo_alineacion_cl",
                "tipo": "interno",
                "nombre_es": "Alineación y balanceado",
                "nombre_en": "Wheel alignment and balancing",
                "precio": 35000,
                "aliases_es": ["alineación", "balanceado"],
                "aliases_en": ["alignment", "balancing"],
            },
            # Reparaciones
            {
                "cat": "demo_reparacion_cl",
                "code": "demo_frenos_cl",
                "tipo": "interno",
                "nombre_es": "Reparación sistema de frenos",
                "nombre_en": "Brake system repair",
                "precio": 80000,
                "aliases_es": ["frenos", "pastillas"],
                "aliases_en": ["brakes", "brake pads"],
            },
            {
                "cat": "demo_reparacion_cl",
                "code": "demo_suspension_cl",
                "tipo": "interno",
                "nombre_es": "Reparación suspensión",
                "nombre_en": "Suspension repair",
                "precio": 120000,
                "aliases_es": ["suspensión", "amortiguadores"],
                "aliases_en": ["suspension", "shock absorbers"],
            },
            # Revisión técnica
            {
                "cat": "demo_revision_cl",
                "code": "demo_revision_tecnica_cl",
                "tipo": "interno",
                "nombre_es": "Revisión técnica vehicular",
                "nombre_en": "Vehicle technical inspection",
                "precio": 15000,
                "aliases_es": ["revisión técnica", "rt"],
                "aliases_en": ["technical inspection", "vehicle inspection"],
            },
            # Servicios externos (subcontratados)
            {
                "cat": "demo_emergencia_cl",
                "code": "demo_grua_cl",
                "tipo": "externo",
                "nombre_es": "Servicio de grúa",
                "nombre_en": "Towing service",
                "precio": 50000,
                "aliases_es": ["grúa", "remolque"],
                "aliases_en": ["towing", "tow truck"],
            },
            {
                "cat": "demo_emergencia_cl",
                "code": "demo_auxilio_cl",
                "tipo": "externo",
                "nombre_es": "Auxilio mecánico en ruta",
                "nombre_en": "Roadside assistance",
                "precio": 30000,
                "aliases_es": ["auxilio", "mecánico en ruta"],
                "aliases_en": ["roadside assistance", "emergency service"],
            },
        ]

        for serv_data in servicios_cl:
            # Buscar categoría
            categoria = CategoriaServicio.objects.filter(code=serv_data["cat"]).first()

            # Crear subcategoría si no existe
            subcat_code = f"sub_{serv_data['code']}"
            subcategoria, created = SubcategoriaServicio.objects.get_or_create(
                categoria=categoria, code=subcat_code, defaults={"country": "CL"}
            )

            if created:
                # Nombres para subcategoría
                SubcategoriaServicioName.objects.create(
                    subcategoria=subcategoria,
                    language="es",
                    label=serv_data["nombre_es"],
                    is_default=True,
                )
                SubcategoriaServicioName.objects.create(
                    subcategoria=subcategoria,
                    language="en",
                    label=serv_data["nombre_en"],
                    is_default=True,
                )

            # Crear servicio
            servicio = Servicio.objects.create(
                subcategoria=subcategoria,
                country="CL",
                tipo=serv_data["tipo"],
                code=serv_data["code"],
                precio_base=Decimal(str(serv_data["precio"])),
            )

            # Nombres en español
            ServicioName.objects.create(
                servicio=servicio,
                language="es",
                label=serv_data["nombre_es"],
                aliases=serv_data["aliases_es"],
                is_default=True,
            )

            # Nombres en inglés
            ServicioName.objects.create(
                servicio=servicio,
                language="en",
                label=serv_data["nombre_en"],
                aliases=serv_data["aliases_en"],
                is_default=True,
            )

            self.datos_creados["servicios"].append(servicio)
            print(f"   ✅ {serv_data['nombre_es']} (${serv_data['precio']:,})")

        print(f"   📊 Total servicios CL: {len(servicios_cl)}\n")

    def crear_servicios_caracteristicos_usa(self):
        """Crear servicios característicos de USA"""
        print("🔧 CREANDO SERVICIOS CARACTERÍSTICOS USA")
        print("-" * 50)

        # Categorías típicas USA
        categorias_us = [
            {
                "code": "demo_maintenance_us",
                "nombre_es": "Mantenimiento",
                "nombre_en": "Maintenance",
            },
            {
                "code": "demo_repair_us",
                "nombre_es": "Reparaciones",
                "nombre_en": "Repairs",
            },
            {
                "code": "demo_inspection_us",
                "nombre_es": "Inspecciones",
                "nombre_en": "Inspections",
            },
            {
                "code": "demo_emergency_us",
                "nombre_es": "Emergencias",
                "nombre_en": "Emergency Services",
            },
        ]

        for cat_data in categorias_us:
            categoria = CategoriaServicio.objects.create(
                country="US", code=cat_data["code"]
            )

            # Nombres en inglés (principal)
            CategoriaServicioName.objects.create(
                categoria=categoria,
                language="en",
                label=cat_data["nombre_en"],
                is_default=True,
            )

            # Nombres en español (secundario)
            CategoriaServicioName.objects.create(
                categoria=categoria,
                language="es",
                label=cat_data["nombre_es"],
                is_default=True,
            )

            print(f"   ✅ Category: {cat_data['nombre_en']}")

        # Servicios específicos de USA
        servicios_us = [
            # Maintenance
            {
                "cat": "demo_maintenance_us",
                "code": "demo_oil_change_us",
                "tipo": "interno",
                "nombre_es": "Cambio de aceite",
                "nombre_en": "Oil Change Service",
                "precio": 45.99,
                "aliases_es": ["aceite"],
                "aliases_en": ["oil change", "lube service"],
            },
            {
                "cat": "demo_maintenance_us",
                "code": "demo_tire_rotation_us",
                "tipo": "interno",
                "nombre_es": "Rotación de neumáticos",
                "nombre_en": "Tire Rotation",
                "precio": 25.99,
                "aliases_es": ["neumáticos", "rotación"],
                "aliases_en": ["tire rotation", "wheel rotation"],
            },
            # Repairs
            {
                "cat": "demo_repair_us",
                "code": "demo_brake_service_us",
                "tipo": "interno",
                "nombre_es": "Servicio de frenos",
                "nombre_en": "Brake Service",
                "precio": 189.99,
                "aliases_es": ["frenos"],
                "aliases_en": ["brake service", "brake repair"],
            },
            {
                "cat": "demo_repair_us",
                "code": "demo_transmission_us",
                "tipo": "interno",
                "nombre_es": "Servicio transmisión",
                "nombre_en": "Transmission Service",
                "precio": 299.99,
                "aliases_es": ["transmisión"],
                "aliases_en": ["transmission", "trans service"],
            },
            # Inspections
            {
                "cat": "demo_inspection_us",
                "code": "demo_state_inspection_us",
                "tipo": "interno",
                "nombre_es": "Inspección estatal",
                "nombre_en": "State Inspection",
                "precio": 18.99,
                "aliases_es": ["inspección"],
                "aliases_en": ["state inspection", "vehicle inspection"],
            },
            # External services
            {
                "cat": "demo_emergency_us",
                "code": "demo_towing_us",
                "tipo": "externo",
                "nombre_es": "Servicio de remolque",
                "nombre_en": "Towing Service",
                "precio": 125.00,
                "aliases_es": ["remolque", "grúa"],
                "aliases_en": ["towing", "tow service"],
            },
            {
                "cat": "demo_emergency_us",
                "code": "demo_roadside_us",
                "tipo": "externo",
                "nombre_es": "Asistencia en carretera",
                "nombre_en": "Roadside Assistance",
                "precio": 89.99,
                "aliases_es": ["asistencia"],
                "aliases_en": ["roadside assistance", "emergency help"],
            },
        ]

        for serv_data in servicios_us:
            # Buscar categoría
            categoria = CategoriaServicio.objects.filter(code=serv_data["cat"]).first()

            # Crear subcategoría si no existe
            subcat_code = f"sub_{serv_data['code']}"
            subcategoria, created = SubcategoriaServicio.objects.get_or_create(
                categoria=categoria, code=subcat_code, defaults={"country": "US"}
            )

            if created:
                # Nombres para subcategoría
                SubcategoriaServicioName.objects.create(
                    subcategoria=subcategoria,
                    language="en",
                    label=serv_data["nombre_en"],
                    is_default=True,
                )
                SubcategoriaServicioName.objects.create(
                    subcategoria=subcategoria,
                    language="es",
                    label=serv_data["nombre_es"],
                    is_default=True,
                )

            # Crear servicio
            servicio = Servicio.objects.create(
                subcategoria=subcategoria,
                country="US",
                tipo=serv_data["tipo"],
                code=serv_data["code"],
                precio_base=Decimal(str(serv_data["precio"])),
            )

            # Nombres en inglés (principal)
            ServicioName.objects.create(
                servicio=servicio,
                language="en",
                label=serv_data["nombre_en"],
                aliases=serv_data["aliases_en"],
                is_default=True,
            )

            # Nombres en español (secundario)
            ServicioName.objects.create(
                servicio=servicio,
                language="es",
                label=serv_data["nombre_es"],
                aliases=serv_data["aliases_es"],
                is_default=True,
            )

            self.datos_creados["servicios"].append(servicio)
            print(f"   ✅ {serv_data['nombre_en']} (${serv_data['precio']})")

        print(f"   📊 Total servicios US: {len(servicios_us)}\n")

    def crear_marcas_modelos_vehiculos(self):
        """Crear marcas y modelos necesarios para los vehículos demo"""
        print("🚗 CREANDO MARCAS Y MODELOS DE VEHÍCULOS")
        print("-" * 50)

        # Crear colores si no existen
        colores = [
            "Blanco",
            "Negro",
            "Gris",
            "Azul",
            "Rojo",
            "Verde",
            "Amarillo",
            "Plata",
        ]

        for color_nombre in colores:
            color, created = ColorVehiculo.objects.get_or_create(nombre=color_nombre)
            if created:
                print(f"   ✅ Color: {color_nombre}")

        # Definir marcas y modelos por país
        marcas_modelos_cl = {
            "Toyota": ["Corolla", "Camry", "RAV4", "Prius"],
            "Ford": ["Fiesta", "Focus"],
            "Chevrolet": ["Spark", "Cruze"],
            "Hyundai": ["Accent", "Elantra"],
            "Nissan": ["Sentra", "Altima"],
            "Kia": ["Rio", "Forte"],
            "Suzuki": ["Swift", "Vitara"],
            "Peugeot": ["208", "308"],
        }

        marcas_modelos_us = {
            "Toyota": ["Corolla", "Camry", "RAV4", "Prius"],
            "Ford": ["F-150", "Explorer"],
            "Chevrolet": ["Silverado", "Equinox"],
            "Honda": ["Civic", "Accord"],
            "Nissan": ["Altima", "Rogue"],
            "Hyundai": ["Elantra", "Tucson"],
            "BMW": ["320i", "328i"],
            "Mercedes": ["C-Class", "E-Class"],
        }

        # Crear marcas y modelos para Chile
        print("   🇨🇱 Marcas y modelos Chile:")
        for marca_nombre, modelos in marcas_modelos_cl.items():
            # Crear marca para CL si no existe
            marca = Marca.objects.filter(nombre=marca_nombre, country="CL").first()
            if not marca:
                marca = Marca.objects.create(nombre=marca_nombre, country="CL")
                print(f"      ✅ Marca CL: {marca_nombre}")

            # Crear modelos para esta marca
            for modelo_nombre in modelos:
                modelo = Modelo.objects.filter(
                    marca=marca, nombre=modelo_nombre, country="CL"
                ).first()
                if not modelo:
                    modelo = Modelo.objects.create(
                        marca=marca, nombre=modelo_nombre, country="CL"
                    )
                    print(f"         ✅ Modelo: {modelo_nombre}")

        # Crear marcas y modelos para USA
        print("   🇺🇸 Marcas y modelos USA:")
        for marca_nombre, modelos in marcas_modelos_us.items():
            # Crear marca para US si no existe
            marca = Marca.objects.filter(nombre=marca_nombre, country="US").first()
            if not marca:
                marca = Marca.objects.create(nombre=marca_nombre, country="US")
                print(f"      ✅ Marca US: {marca_nombre}")

            # Crear modelos para esta marca
            for modelo_nombre in modelos:
                modelo = Modelo.objects.filter(
                    marca=marca, nombre=modelo_nombre, country="US"
                ).first()
                if not modelo:
                    modelo = Modelo.objects.create(
                        marca=marca, nombre=modelo_nombre, country="US"
                    )
                    print(f"         ✅ Modelo: {modelo_nombre}")

        total_marcas_cl = len(marcas_modelos_cl)
        total_marcas_us = len(marcas_modelos_us)
        total_modelos_cl = sum(len(modelos) for modelos in marcas_modelos_cl.values())
        total_modelos_us = sum(len(modelos) for modelos in marcas_modelos_us.values())

        print(f"   📊 Total marcas CL: {total_marcas_cl}")
        print(f"   📊 Total modelos CL: {total_modelos_cl}")
        print(f"   📊 Total marcas US: {total_marcas_us}")
        print(f"   📊 Total modelos US: {total_modelos_us}\n")

    def crear_clientes_y_vehiculos_chile(self):
        """Crear clientes y vehículos realistas para Chile"""
        print("👥 CREANDO CLIENTES Y VEHÍCULOS CHILE")
        print("-" * 50)

        empresas_cl = Empresa.objects.filter(pais="CL")

        # Obtener o crear regiones chilenas
        region_rm, _ = TallerRegion.objects.get_or_create(
            nombre="Región Metropolitana", defaults={"country": "CL"}
        )
        ciudad_santiago, _ = TallerCiudad.objects.get_or_create(
            nombre="Santiago", region=region_rm, defaults={"country": "CL"}
        )

        clientes_cl = [
            {
                "nombre": "Juan Carlos",
                "apellido": "Pérez González",
                "telefono": "+56 9 8765 4321",
                "email": "jperez@email.cl",
                "vehiculos": [
                    {
                        "marca": "Toyota",
                        "modelo": "Corolla",
                        "año": 2019,
                        "patente": "ABCD12",
                    },
                    {
                        "marca": "Chevrolet",
                        "modelo": "Spark",
                        "año": 2020,
                        "patente": "EFGH34",
                    },
                ],
            },
            {
                "nombre": "María Elena",
                "apellido": "Silva Rodríguez",
                "telefono": "+56 9 7654 3210",
                "email": "msilva@gmail.com",
                "vehiculos": [
                    {
                        "marca": "Hyundai",
                        "modelo": "Accent",
                        "año": 2018,
                        "patente": "IJKL56",
                    }
                ],
            },
            {
                "nombre": "Carlos Alberto",
                "apellido": "Morales Castro",
                "telefono": "+56 9 6543 2109",
                "email": "cmorales@outlook.cl",
                "vehiculos": [
                    {
                        "marca": "Nissan",
                        "modelo": "Sentra",
                        "año": 2021,
                        "patente": "MNOP78",
                    },
                    {"marca": "Kia", "modelo": "Rio", "año": 2017, "patente": "QRST90"},
                ],
            },
            {
                "nombre": "Andrea",
                "apellido": "Fernández López",
                "telefono": "+56 9 5432 1098",
                "email": "afernandez@empresa.cl",
                "vehiculos": [
                    {
                        "marca": "Suzuki",
                        "modelo": "Swift",
                        "año": 2019,
                        "patente": "UVWX12",
                    }
                ],
            },
            {
                "nombre": "Roberto",
                "apellido": "Muñoz Henríquez",
                "telefono": "+56 9 4321 0987",
                "email": "rmunoz@hotmail.com",
                "vehiculos": [
                    {
                        "marca": "Ford",
                        "modelo": "Fiesta",
                        "año": 2020,
                        "patente": "YZAB34",
                    },
                    {
                        "marca": "Peugeot",
                        "modelo": "208",
                        "año": 2018,
                        "patente": "CDEF56",
                    },
                ],
            },
        ]

        for empresa in empresas_cl:
            for cliente_data in clientes_cl:
                # Crear cliente
                cliente = Cliente.objects.create(
                    empresa=empresa,
                    nombre=cliente_data["nombre"],
                    apellido=cliente_data["apellido"],
                    telefono=cliente_data["telefono"],
                    email=cliente_data["email"],
                    region=region_rm,
                    ciudad=ciudad_santiago,
                    direccion=f"Calle Demo {random.randint(100, 999)}, Santiago",
                )

                self.datos_creados["clientes"].append(cliente)

                # Crear vehículos para este cliente
                for vehiculo_data in cliente_data["vehiculos"]:
                    # Buscar marca y modelo para Chile
                    marca = Marca.objects.filter(
                        nombre=vehiculo_data["marca"], country="CL"
                    ).first()
                    modelo = Modelo.objects.filter(
                        marca=marca, nombre=vehiculo_data["modelo"], country="CL"
                    ).first()
                    color = (
                        ColorVehiculo.objects.filter(
                            nombre__in=["Blanco", "Negro", "Gris", "Azul", "Rojo"]
                        )
                        .order_by("?")
                        .first()
                    )

                    vehiculo = Vehiculo.objects.create(
                        empresa=empresa,
                        cliente=cliente,
                        marca=marca,
                        modelo=modelo,
                        anio=vehiculo_data["año"],
                        patente=vehiculo_data["patente"],
                        color=color,
                    )

                    self.datos_creados["vehiculos"].append(vehiculo)

                print(
                    f"   ✅ {cliente.nombre} {cliente.apellido} ({len(cliente_data['vehiculos'])} vehículos)"
                )

            print(
                f"   📊 Empresa: {empresa.nombre_taller} - {len(clientes_cl)} clientes"
            )

        print(f"   📊 Total clientes CL: {len(clientes_cl) * len(empresas_cl)}\n")

    def crear_clientes_y_vehiculos_usa(self):
        """Crear clientes y vehículos realistas para USA"""
        print("👥 CREANDO CLIENTES Y VEHÍCULOS USA")
        print("-" * 50)

        empresas_us = Empresa.objects.filter(pais="US")

        clientes_us = [
            {
                "nombre": "Michael",
                "apellido": "Johnson",
                "telefono": "+1 305 555 1234",
                "email": "mjohnson@email.com",
                "vehiculos": [
                    {
                        "marca": "Ford",
                        "modelo": "F-150",
                        "año": 2020,
                        "patente": "ABC123",
                    },
                    {
                        "marca": "Honda",
                        "modelo": "Civic",
                        "año": 2019,
                        "patente": "DEF456",
                    },
                ],
            },
            {
                "nombre": "Sarah",
                "apellido": "Williams",
                "telefono": "+1 323 555 5678",
                "email": "swilliams@gmail.com",
                "vehiculos": [
                    {
                        "marca": "Toyota",
                        "modelo": "Camry",
                        "año": 2021,
                        "patente": "GHI789",
                    }
                ],
            },
            {
                "nombre": "David",
                "apellido": "Brown",
                "telefono": "+1 214 555 9012",
                "email": "dbrown@company.com",
                "vehiculos": [
                    {
                        "marca": "Chevrolet",
                        "modelo": "Silverado",
                        "año": 2018,
                        "patente": "JKL012",
                    },
                    {
                        "marca": "Nissan",
                        "modelo": "Altima",
                        "año": 2020,
                        "patente": "MNO345",
                    },
                ],
            },
            {
                "nombre": "Jennifer",
                "apellido": "Davis",
                "telefono": "+1 305 555 3456",
                "email": "jdavis@outlook.com",
                "vehiculos": [
                    {
                        "marca": "Hyundai",
                        "modelo": "Elantra",
                        "año": 2019,
                        "patente": "PQR678",
                    }
                ],
            },
            {
                "nombre": "Robert",
                "apellido": "Miller",
                "telefono": "+1 323 555 7890",
                "email": "rmiller@hotmail.com",
                "vehiculos": [
                    {
                        "marca": "BMW",
                        "modelo": "320i",
                        "año": 2020,
                        "patente": "STU901",
                    },
                    {
                        "marca": "Mercedes",
                        "modelo": "C-Class",
                        "año": 2018,
                        "patente": "VWX234",
                    },
                ],
            },
        ]

        for empresa in empresas_us:
            for cliente_data in clientes_us:
                # Crear cliente
                cliente = Cliente.objects.create(
                    empresa=empresa,
                    nombre=cliente_data["nombre"],
                    apellido=cliente_data["apellido"],
                    telefono=cliente_data["telefono"],
                    email=cliente_data["email"],
                    direccion=f"{random.randint(100, 999)} Demo Street, Demo City",
                )

                self.datos_creados["clientes"].append(cliente)

                # Crear vehículos para este cliente
                for vehiculo_data in cliente_data["vehiculos"]:
                    # Buscar marca y modelo para USA
                    marca = Marca.objects.filter(
                        nombre=vehiculo_data["marca"], country="US"
                    ).first()
                    modelo = Modelo.objects.filter(
                        marca=marca, nombre=vehiculo_data["modelo"], country="US"
                    ).first()
                    color = (
                        ColorVehiculo.objects.filter(
                            nombre__in=["Blanco", "Negro", "Gris", "Azul", "Rojo"]
                        )
                        .order_by("?")
                        .first()
                    )

                    vehiculo = Vehiculo.objects.create(
                        empresa=empresa,
                        cliente=cliente,
                        marca=marca,
                        modelo=modelo,
                        anio=vehiculo_data["año"],
                        patente=vehiculo_data["patente"],
                        color=color,
                    )

                    self.datos_creados["vehiculos"].append(vehiculo)

                print(
                    f"   ✅ {cliente.nombre} {cliente.apellido} ({len(cliente_data['vehiculos'])} vehicles)"
                )

            print(
                f"   📊 Company: {empresa.nombre_taller} - {len(clientes_us)} clients"
            )

        print(f"   📊 Total clients US: {len(clientes_us) * len(empresas_us)}\n")

    def generar_fixtures_completas(self):
        """Generar todas las fixtures de forma ordenada"""
        print("🚀 GENERANDO FIXTURES REALISTAS COMPLETAS")
        print("🎯 Datos demo coherentes, variados y útiles")
        print("=" * 80)

        try:
            # Paso 1: Limpiar datos anteriores
            self.limpiar_datos_demo_anteriores()

            # Paso 2: Crear marcas y modelos
            self.crear_marcas_modelos_vehiculos()

            # Paso 3: Crear empresas
            self.crear_empresas_demo_chile()
            self.crear_empresas_demo_usa()

            # Paso 4: Crear servicios característicos
            self.crear_servicios_caracteristicos_chile()
            self.crear_servicios_caracteristicos_usa()

            # Paso 5: Crear clientes y vehículos
            self.crear_clientes_y_vehiculos_chile()
            self.crear_clientes_y_vehiculos_usa()

            # Reporte final
            self.generar_reporte_fixtures()

            return True

        except Exception as e:
            print(f"\n💥 ERROR EN GENERACIÓN DE FIXTURES: {e}")
            import traceback

            traceback.print_exc()
            return False

    def generar_reporte_fixtures(self):
        """Generar reporte final de fixtures creadas"""
        print("=" * 80)
        print("📊 REPORTE FINAL DE FIXTURES GENERADAS")
        print("=" * 80)

        # Contar totales
        total_usuarios = len(self.datos_creados["usuarios"])
        total_empresas = len(self.datos_creados["empresas"])
        total_clientes = len(self.datos_creados["clientes"])
        total_vehiculos = len(self.datos_creados["vehiculos"])
        total_servicios = len(self.datos_creados["servicios"])

        print(f"👤 Usuarios creados: {total_usuarios}")
        print(f"🏢 Empresas creadas: {total_empresas}")
        print(f"👥 Clientes creados: {total_clientes}")
        print(f"🚗 Vehículos creados: {total_vehiculos}")
        print(f"🔧 Servicios creados: {total_servicios}")

        # Estadísticas por país
        empresas_cl = Empresa.objects.filter(pais="CL").count()
        empresas_us = Empresa.objects.filter(pais="US").count()
        servicios_cl = Servicio.objects.filter(
            country="CL", code__contains="demo_"
        ).count()
        servicios_us = Servicio.objects.filter(
            country="US", code__contains="demo_"
        ).count()

        print(f"\n🇨🇱 CHILE:")
        print(f"   Empresas: {empresas_cl}")
        print(f"   Servicios: {servicios_cl}")

        print(f"\n🇺🇸 USA:")
        print(f"   Empresas: {empresas_us}")
        print(f"   Servicios: {servicios_us}")

        print(f"\n✨ CARACTERÍSTICAS DESTACADAS:")
        print("   🎯 Datos realistas por mercado")
        print("   🌍 Localización completa ES/EN")
        print("   🔧 Servicios característicos por país")
        print("   👥 Clientes con múltiples vehículos")
        print("   💰 Precios en moneda local")
        print("   📱 Contactos y direcciones reales")

        print(f"\n🔐 CREDENCIALES DE ACCESO:")
        print("   Username pattern: demo_[nombre]_[ciudad]")
        print("   Password para todos: demo2025")
        print("   Ejemplos:")
        print("   - demo_taller_santiago / demo2025")
        print("   - demo_mikes_auto_miami / demo2025")

        print(f"\n🎉 FIXTURES COMPLETADAS EXITOSAMENTE")
        print("✅ Sistema listo para pruebas funcionales completas")


if __name__ == "__main__":
    generator = FixturesRealesGenerator()
    generator.generar_fixtures_completas()
