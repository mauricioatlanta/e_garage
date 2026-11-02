"""
Comando para asignar región y ciudad a todos los clientes chilenos que no las tengan.
"""

import random

from django.core.management.base import BaseCommand
from django.db import models

from taller.models.clientes import Cliente
from taller.models.region_ciudad import TallerCiudad, TallerRegion


class Command(BaseCommand):
    help = "Asigna región y ciudad a todos los clientes chilenos que no las tengan"

    def add_arguments(self, parser):
        parser.add_argument(
            "--empresa",
            type=str,
            default=None,
            help="Nombre de la empresa (opcional, si no se especifica se aplica a todas)",
        )
        parser.add_argument(
            "--region",
            type=str,
            default=None,
            help="Nombre de la región específica a asignar (opcional)",
        )

    def handle(self, *args, **options):
        empresa_nombre = options.get("empresa")
        region_nombre = options.get("region")

        # Obtener todas las regiones de Chile
        regiones = TallerRegion.objects.all()
        if not regiones.exists():
            self.stdout.write(
                self.style.ERROR(
                    "❌ No hay regiones en la base de datos. Ejecuta primero: python manage.py cargar_regiones"
                )
            )
            return

        # Filtrar clientes chilenos sin región o ciudad
        clientes_qs = Cliente.objects.filter(empresa__pais="CL").filter(
            models.Q(region__isnull=True) | models.Q(ciudad__isnull=True)
        )

        if empresa_nombre:
            clientes_qs = clientes_qs.filter(empresa__nombre_taller__icontains=empresa_nombre)

        total_clientes = clientes_qs.count()

        if total_clientes == 0:
            self.stdout.write(
                self.style.SUCCESS("✅ Todos los clientes ya tienen región y ciudad asignadas")
            )
            return

        self.stdout.write(f"📋 Encontrados {total_clientes} clientes sin región o ciudad")

        # Si se especifica una región, usarla; si no, usar una aleatoria
        if region_nombre:
            try:
                region_objetivo = TallerRegion.objects.get(nombre__icontains=region_nombre)
                self.stdout.write(f"📍 Usando región específica: {region_objetivo.nombre}")
            except TallerRegion.DoesNotExist:
                self.stdout.write(self.style.ERROR(f"❌ No se encontró la región: {region_nombre}"))
                return
        else:
            region_objetivo = None

        actualizados = 0
        errores = 0

        for cliente in clientes_qs:
            try:
                # Seleccionar región
                if region_objetivo:
                    region = region_objetivo
                else:
                    region = random.choice(list(regiones))

                # Obtener ciudades de esa región
                ciudades_region = TallerCiudad.objects.filter(region=region)

                if not ciudades_region.exists():
                    self.stdout.write(
                        self.style.WARNING(
                            f"⚠️  La región {region.nombre} no tiene ciudades. Creando ciudad por defecto..."
                        )
                    )
                    ciudad = TallerCiudad.objects.create(
                        nombre=f"{region.nombre} - Ciudad Principal", region=region
                    )
                else:
                    ciudad = random.choice(list(ciudades_region))

                # Asignar región y ciudad al cliente
                cliente.region = region
                cliente.ciudad = ciudad
                cliente.save(update_fields=["region", "ciudad"])

                actualizados += 1

                if actualizados % 10 == 0:
                    self.stdout.write(
                        f"  ✓ Actualizados {actualizados}/{total_clientes} clientes..."
                    )

            except Exception as e:
                errores += 1
                self.stdout.write(
                    self.style.ERROR(f"  ✗ Error al actualizar cliente {cliente.pk}: {str(e)}")
                )

        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS(f"✅ Proceso completado:"))
        self.stdout.write(f"   ✓ Clientes actualizados: {actualizados}")
        if errores > 0:
            self.stdout.write(self.style.WARNING(f"   ⚠️  Errores: {errores}"))
