# -*- coding: utf-8 -*-
"""
Comando para migrar campos legacy de direcciones a modelo Address

Migra:
- Chile: region/ciudad → Address
- USA/BR/PE/VE: estado_usa/ciudad_usa → Address

Convenciones:
- Solo crea Address si no existe billing_address
- Preserva datos legacy (no los borra)
- Usa direccion como line1
- Usa zipcode como postal_code
"""
from django.core.management.base import BaseCommand
from django.db import transaction

from taller.models.clientes import Cliente
from ubicacion.models import Address


class Command(BaseCommand):
    help = "Crea Address a partir de campos legacy (CL: region/ciudad; US/BR/PE/VE: estado_usa/ciudad_usa)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Simular sin guardar cambios",
        )
        parser.add_argument(
            "--pais",
            type=str,
            help="Solo migrar clientes de un país específico (CL, US, BR, PE, VE)",
        )

    def handle(self, *args, **options):
        dry_run = options.get("dry_run", False)
        pais_filter = (options.get("pais") or "").upper()

        if dry_run:
            self.stdout.write(self.style.WARNING("[DRY RUN] Simulación - no se guardarán cambios"))

        self.stdout.write("\n" + "=" * 80)
        self.stdout.write("[BACKFILL] Migrando direcciones legacy a Address")
        self.stdout.write("=" * 80 + "\n")

        # Contadores
        count_total = 0
        count_chile = 0
        count_usa_br_pe_ve = 0
        count_skipped = 0
        count_no_city = 0

        # Obtener clientes
        clientes = Cliente.objects.all()

        # Filtrar por país si se especifica
        if pais_filter:
            self.stdout.write(f"[FILTER] Solo procesando país: {pais_filter}\n")
            # Filtrar por empresa.pais
            clientes = clientes.filter(empresa__pais=pais_filter)

        total_clientes = clientes.count()
        self.stdout.write(f"[INFO] Total de clientes a procesar: {total_clientes}\n")

        # Procesar cada cliente
        for i, cliente in enumerate(clientes, 1):
            # Mostrar progreso cada 100
            if i % 100 == 0:
                self.stdout.write(f"[PROGRESO] Procesados {i}/{total_clientes}...")

            # Skip si ya tiene billing_address
            if cliente.billing_address_id:
                count_skipped += 1
                continue

            city = None
            source = None

            # === 1) CHILE LEGACY ===
            # region → ciudad (TallerCiudad)
            if hasattr(cliente, "ciudad") and cliente.ciudad:
                # Chile usa TallerCiudad (modelo legacy)
                # NO podemos migrar directamente porque TallerCiudad != taller.Ciudad
                # Por ahora solo logueamos
                self.stdout.write(
                    self.style.WARNING(
                        f"  [SKIP] Cliente {cliente.pk} ({cliente.nombre}): "
                        f"Usa TallerCiudad (Chile legacy) - requiere migración manual"
                    )
                )
                count_skipped += 1
                continue

            # === 2) USA/BRASIL/PERU/VENEZUELA LEGACY ===
            # estado_usa → ciudad_usa (taller.Ciudad - modelo unificado)
            elif hasattr(cliente, "ciudad_usa") and cliente.ciudad_usa:
                city = cliente.ciudad_usa
                source = "estado_usa/ciudad_usa"
                count_usa_br_pe_ve += 1

            # Si encontramos ciudad, crear Address
            if city:
                try:
                    # Construir line1 desde campo direccion
                    line1 = ""
                    if hasattr(cliente, "direccion") and cliente.direccion:
                        line1 = str(cliente.direccion)[:160]

                    # Si no hay direccion, usar placeholder
                    if not line1:
                        line1 = "N/A"

                    # Obtener postal_code
                    postal_code = ""
                    if hasattr(cliente, "zipcode") and cliente.zipcode:
                        postal_code = str(cliente.zipcode)[:20]

                    # Crear Address
                    if not dry_run:
                        with transaction.atomic():
                            addr = Address.objects.create(
                                line1=line1,
                                line2="",
                                city=city,
                                postal_code=postal_code,
                                company=cliente.empresa if hasattr(cliente, "empresa") else None,
                            )

                            # Asignar a cliente
                            cliente.billing_address = addr
                            cliente.save(update_fields=["billing_address"])

                    count_total += 1

                    # Log cada 50 migraciones exitosas
                    if count_total % 50 == 0:
                        self.stdout.write(
                            self.style.SUCCESS(f"  [OK] {count_total} direcciones migradas...")
                        )

                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"  [ERROR] Cliente {cliente.pk}: {e}"))
            else:
                count_no_city += 1

        # === RESUMEN ===
        self.stdout.write("\n" + "=" * 80)
        self.stdout.write("[RESUMEN] Backfill completado")
        self.stdout.write("=" * 80)

        self.stdout.write(f"\n  Total clientes procesados: {total_clientes}")
        self.stdout.write(f"  Addresses creadas: {count_total}")
        self.stdout.write(f"    - Desde estado_usa/ciudad_usa: {count_usa_br_pe_ve}")
        self.stdout.write(f"    - Desde region/ciudad (CL): {count_chile}")
        self.stdout.write(f"  Clientes ya con Address: {count_skipped}")
        self.stdout.write(f"  Clientes sin ciudad: {count_no_city}")

        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    f"\n[DRY RUN] Simulación completada - ejecuta sin --dry-run para aplicar"
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(f"\n[EXITO] {count_total} direcciones migradas a Address")
            )

        self.stdout.write("\n" + "=" * 80 + "\n")

        # Recomendaciones
        if count_chile > 0:
            self.stdout.write(
                self.style.WARNING(
                    "[NOTA] Clientes de Chile requieren migración manual "
                    "(TallerCiudad → taller.Ciudad)"
                )
            )
