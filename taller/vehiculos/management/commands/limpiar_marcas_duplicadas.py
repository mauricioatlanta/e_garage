"""
Comando de gestión para limpiar marcas duplicadas por nombre dentro del mismo país
Ejecutar: python manage.py limpiar_marcas_duplicadas --country CL
"""

from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import Count

from taller.models.marca import Marca


class Command(BaseCommand):
    help = "Elimina marcas duplicadas por nombre dentro del mismo país, manteniendo solo la primera"

    def add_arguments(self, parser):
        parser.add_argument(
            "--country",
            type=str,
            default="CL",
            help="País a limpiar (CL, US, MX). Por defecto: CL",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Solo mostrar qué se eliminaría sin hacer cambios",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        country = options["country"]
        dry_run = options["dry_run"]

        if dry_run:
            self.stdout.write(self.style.WARNING("🔍 MODO DRY-RUN: No se harán cambios\n"))

        # Encontrar duplicados por nombre (case-insensitive) dentro del mismo país
        marcas = Marca.objects.filter(country=country).order_by("nombre", "id")

        # Agrupar por nombre (case-insensitive)
        nombres_vistos = {}
        duplicados_encontrados = []
        marcas_a_eliminar = []

        for marca in marcas:
            nombre_key = marca.nombre.lower().strip()

            if nombre_key in nombres_vistos:
                # Es un duplicado
                duplicados_encontrados.append(marca)
                marcas_a_eliminar.append(marca)
                self.stdout.write(
                    f"  ⚠️ Duplicado encontrado: '{marca.nombre}' (ID: {marca.id}) - "
                    f"Ya existe ID: {nombres_vistos[nombre_key]}"
                )
            else:
                # Primera ocurrencia, mantenerla
                nombres_vistos[nombre_key] = marca.id

        if not duplicados_encontrados:
            self.stdout.write(
                self.style.SUCCESS(f"✅ No se encontraron duplicados para país {country}")
            )
            return

        self.stdout.write(
            f"\n📊 Resumen: {len(duplicados_encontrados)} marca(s) duplicada(s) encontrada(s)"
        )

        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    f"\n🔍 DRY-RUN: Se eliminarían {len(marcas_a_eliminar)} marca(s) duplicada(s)"
                )
            )
        else:
            # Eliminar duplicados
            ids_eliminados = [m.id for m in marcas_a_eliminar]
            Marca.objects.filter(id__in=ids_eliminados).delete()

            self.stdout.write(
                self.style.SUCCESS(f"✅ Eliminadas {len(marcas_a_eliminar)} marca(s) duplicada(s)")
            )



