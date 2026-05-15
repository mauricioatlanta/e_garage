# -*- coding: utf-8 -*-
"""
Comando para migrar tax_id a tax_id_type automáticamente

Auto-detecta el tipo de tax_id según:
- País de la empresa
- Formato del tax_id (heurística)

Convenciones:
- Chile → CL_RUT
- USA → US_EIN o US_SSN (detecta por formato)
- Brasil → BR_CPF o BR_CNPJ (detecta por longitud)
- Perú → PE_RUC
- Venezuela → VE_RIF
"""
from django.core.management.base import BaseCommand
from django.db import transaction

from taller.models.clientes import Cliente


class Command(BaseCommand):
    help = "Auto-detecta y asigna tax_id_type según país y formato del tax_id"

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Simular sin guardar cambios",
        )
        parser.add_argument(
            "--force",
            action="store_true",
            help="Actualizar incluso si tax_id_type ya está configurado",
        )

    def handle(self, *args, **options):
        dry_run = options.get("dry_run", False)
        force = options.get("force", False)

        if dry_run:
            self.stdout.write(self.style.WARNING("[DRY RUN] Simulación - no se guardarán cambios"))

        self.stdout.write("\n" + "=" * 80)
        self.stdout.write("[BACKFILL] Auto-detectando tax_id_type")
        self.stdout.write("=" * 80 + "\n")

        # Contadores
        count_updated = 0
        count_skipped = 0
        count_no_tax_id = 0
        count_no_empresa = 0

        # Mapeo país → tax_id_type por defecto
        PAIS_TO_TAX_ID = {
            "CL": "CL_RUT",
            "US": "US_EIN",  # Por defecto EIN, se refina por formato
            "BR": "BR_CPF",  # Por defecto CPF, se refina por longitud
            "PE": "PE_RUC",
            "VE": "VE_RIF",
        }

        # Obtener clientes con tax_id
        clientes = Cliente.objects.exclude(tax_id="").exclude(tax_id__isnull=True)

        total = clientes.count()
        self.stdout.write(f"[INFO] Total de clientes con tax_id: {total}\n")

        for i, cliente in enumerate(clientes, 1):
            # Progreso cada 100
            if i % 100 == 0:
                self.stdout.write(f"[PROGRESO] Procesados {i}/{total}...")

            # Skip si ya tiene tax_id_type configurado (y no es force)
            if not force and cliente.tax_id_type and cliente.tax_id_type != "CL_RUT":
                # CL_RUT es el default, así que si no es CL_RUT significa que ya se configuró
                count_skipped += 1
                continue

            # Obtener país de la empresa
            if not hasattr(cliente, "empresa") or not cliente.empresa:
                count_no_empresa += 1
                continue

            pais = cliente.empresa.pais

            # Auto-detectar tipo
            tax_id_type = self._detect_tax_id_type(cliente.tax_id, pais)

            # Actualizar
            if tax_id_type:
                if not dry_run:
                    try:
                        with transaction.atomic():
                            cliente.tax_id_type = tax_id_type
                            cliente.save(update_fields=["tax_id_type"])
                        count_updated += 1
                    except Exception as e:
                        self.stdout.write(self.style.ERROR(f"  [ERROR] Cliente {cliente.pk}: {e}"))
                else:
                    count_updated += 1
                    # En dry-run, solo contar

                # Log cada 50 actualizaciones
                if count_updated % 50 == 0:
                    self.stdout.write(
                        self.style.SUCCESS(f"  [OK] {count_updated} tax_id_types asignados...")
                    )

        # === RESUMEN ===
        self.stdout.write("\n" + "=" * 80)
        self.stdout.write("[RESUMEN] Backfill completado")
        self.stdout.write("=" * 80)

        self.stdout.write(f"\n  Total clientes con tax_id: {total}")
        self.stdout.write(f"  Tax ID types asignados: {count_updated}")
        self.stdout.write(f"  Ya configurados (skipped): {count_skipped}")
        self.stdout.write(f"  Sin empresa: {count_no_empresa}")

        if dry_run:
            self.stdout.write(
                self.style.WARNING(f"\n[DRY RUN] Ejecuta sin --dry-run para aplicar cambios")
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(f"\n[EXITO] {count_updated} tax_id_types actualizados")
            )

        self.stdout.write("\n" + "=" * 80 + "\n")

    def _detect_tax_id_type(self, tax_id: str, pais: str) -> str:
        """
        Auto-detecta el tipo de tax_id según formato y país.

        Args:
            tax_id: Valor del tax_id
            pais: Código de país (CL, US, BR, PE, VE)

        Returns:
            Código de tax_id_type detectado
        """
        if not tax_id:
            return None

        # Limpiar para análisis
        digits_only = "".join(filter(str.isdigit, tax_id))

        if pais == "CL":
            return "CL_RUT"

        elif pais == "US":
            # USA: Distinguir entre EIN y SSN por formato
            if len(digits_only) == 9:
                # SSN típicamente tiene formato XXX-XX-XXXX (3 grupos)
                # EIN típicamente tiene formato XX-XXXXXXX (2 grupos)
                if tax_id.count("-") == 2:
                    return "US_SSN"
                else:
                    return "US_EIN"  # Default para empresas
            return "US_EIN"

        elif pais == "BR":
            # Brasil: Distinguir entre CPF (11) y CNPJ (14)
            if len(digits_only) == 11:
                return "BR_CPF"  # Pessoa física
            elif len(digits_only) == 14:
                return "BR_CNPJ"  # Pessoa jurídica
            return "BR_CPF"  # Default

        elif pais == "PE":
            return "PE_RUC"

        elif pais == "VE":
            return "VE_RIF"

        # Default según país
        PAIS_TO_TAX_ID = {
            "CL": "CL_RUT",
            "US": "US_EIN",
            "BR": "BR_CPF",
            "PE": "PE_RUC",
            "VE": "VE_RIF",
        }

        return PAIS_TO_TAX_ID.get(pais, "CL_RUT")
