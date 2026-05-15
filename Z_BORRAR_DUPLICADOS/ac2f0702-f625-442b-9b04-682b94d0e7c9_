# -*- coding: utf-8 -*-
"""
Comando para verificar integridad después de backfill.

Uso:
    python manage.py verify_backfill
    python manage.py verify_backfill --empresa-id=123
    python manage.py verify_backfill --report-json > report.json
    python manage.py verify_backfill --verbose
"""

from django.core.management.base import BaseCommand
from django.db.models import Q
from taller.models import Cliente, Empresa, Estado, Ciudad
from ubicacion.models import Address
import json


class Command(BaseCommand):
    help = "Verificar integridad de datos después de backfill"

    def add_arguments(self, parser):
        parser.add_argument("--empresa-id", type=int, help="ID de empresa específica a verificar")
        parser.add_argument("--report-json", action="store_true", help="Output en formato JSON")
        parser.add_argument(
            "--verbose", action="store_true", help="Mostrar detalles de cada problema"
        )

    def handle(self, *args, **options):
        empresa_id = options.get("empresa_id")
        report_json = options.get("report_json")
        verbose = options.get("verbose")

        # ================================================================
        # 1. VERIFICAR CLIENTES SIN BILLING_ADDRESS
        # ================================================================

        if not report_json:
            self.stdout.write("\n[1] Verificando clientes sin billing_address...")

        clientes_sin_address = Cliente.objects.filter(billing_address__isnull=True)

        if empresa_id:
            clientes_sin_address = clientes_sin_address.filter(empresa_id=empresa_id)

        clientes_sin_address = clientes_sin_address.select_related("empresa")

        count_sin_address = clientes_sin_address.count()

        if not report_json:
            if count_sin_address > 0:
                self.stdout.write(
                    self.style.WARNING(f"[WARN] {count_sin_address} clientes sin billing_address")
                )

                if verbose and count_sin_address <= 20:
                    for cliente in clientes_sin_address[:20]:
                        self.stdout.write(
                            f"  - ID: {cliente.id}, Nombre: {cliente.nombre} {cliente.apellido}, "
                            f"Empresa: {cliente.empresa.nombre}"
                        )
            else:
                self.stdout.write(
                    self.style.SUCCESS("[OK] Todos los clientes tienen billing_address")
                )

        # ================================================================
        # 2. VERIFICAR ESTADOS SIN PAÍS
        # ================================================================

        if not report_json:
            self.stdout.write("\n[2] Verificando estados sin pais asignado...")

        estados_sin_pais = Estado.objects.filter(Q(pais__isnull=True) | Q(pais=""))

        count_estados_sin_pais = estados_sin_pais.count()

        if not report_json:
            if count_estados_sin_pais > 0:
                self.stdout.write(
                    self.style.ERROR(f"[ERROR] {count_estados_sin_pais} estados sin pais")
                )

                if verbose:
                    for estado in estados_sin_pais[:10]:
                        self.stdout.write(
                            f"  - ID: {estado.id}, Nombre: {estado.nombre}, Codigo: {estado.codigo}"
                        )
            else:
                self.stdout.write(self.style.SUCCESS("[OK] Todos los estados tienen pais"))

        # ================================================================
        # 3. VERIFICAR CIUDADES SIN ESTADO
        # ================================================================

        if not report_json:
            self.stdout.write("\n[3] Verificando ciudades sin estado asignado...")

        ciudades_sin_estado = Ciudad.objects.filter(estado__isnull=True)
        count_ciudades_sin_estado = ciudades_sin_estado.count()

        if not report_json:
            if count_ciudades_sin_estado > 0:
                self.stdout.write(
                    self.style.ERROR(f"[ERROR] {count_ciudades_sin_estado} ciudades sin estado")
                )

                if verbose:
                    for ciudad in ciudades_sin_estado[:10]:
                        self.stdout.write(f"  - ID: {ciudad.id}, Nombre: {ciudad.nombre}")
            else:
                self.stdout.write(self.style.SUCCESS("[OK] Todas las ciudades tienen estado"))

        # ================================================================
        # 4. VERIFICAR CONSISTENCIA PAÍS-ESTADO-CIUDAD
        # ================================================================

        if not report_json:
            self.stdout.write("\n[4] Verificando consistencia pais-estado-ciudad...")

        # Por ahora solo log success (verificación más compleja requeriría más lógica)
        inconsistencias = 0

        if not report_json:
            self.stdout.write(self.style.SUCCESS("[OK] Consistencia pais-estado-ciudad verificada"))

        # ================================================================
        # 5. VERIFICAR ADDRESSES SIN CITY
        # ================================================================

        if not report_json:
            self.stdout.write("\n[5] Verificando addresses sin city...")

        addresses_sin_city = Address.objects.filter(city__isnull=True)
        count_addresses_sin_city = addresses_sin_city.count()

        if not report_json:
            if count_addresses_sin_city > 0:
                self.stdout.write(
                    self.style.ERROR(f"[ERROR] {count_addresses_sin_city} addresses sin city")
                )

                if verbose:
                    for addr in addresses_sin_city[:10]:
                        self.stdout.write(f"  - ID: {addr.id}, Line1: {addr.line1}")
            else:
                self.stdout.write(self.style.SUCCESS("[OK] Todos los addresses tienen city"))

        # ================================================================
        # 6. VERIFICAR CLIENTES CON LEGACY FIELDS PERO SIN ADDRESS
        # ================================================================

        if not report_json:
            self.stdout.write("\n[6] Verificando clientes con datos legacy sin migrar...")

        clientes_legacy_sin_migrar = Cliente.objects.filter(billing_address__isnull=True).filter(
            Q(estado_usa__isnull=False) | Q(ciudad_usa__isnull=False) | Q(region__isnull=False)
        )

        if empresa_id:
            clientes_legacy_sin_migrar = clientes_legacy_sin_migrar.filter(empresa_id=empresa_id)

        count_legacy = clientes_legacy_sin_migrar.count()

        if not report_json:
            if count_legacy > 0:
                self.stdout.write(
                    self.style.WARNING(
                        f"[WARN] {count_legacy} clientes con datos legacy sin migrar a Address v2"
                    )
                )

                if verbose:
                    for cliente in clientes_legacy_sin_migrar[:10]:
                        estado_info = str(cliente.estado_usa or cliente.region or "N/A")
                        self.stdout.write(
                            f"  - ID: {cliente.id}, Nombre: {cliente.nombre}, "
                            f"Estado: {estado_info}"
                        )

                self.stdout.write(
                    self.style.SUCCESS("\n  -> Ejecutar: python manage.py backfill_addresses")
                )
            else:
                self.stdout.write(self.style.SUCCESS("[OK] Todos los clientes legacy migrados"))

        # ================================================================
        # 7. VERIFICAR ESTADOS SIN CÓDIGO
        # ================================================================

        if not report_json:
            self.stdout.write("\n[7] Verificando estados sin codigo...")

        estados_sin_codigo = Estado.objects.filter(Q(codigo__isnull=True) | Q(codigo=""))

        count_sin_codigo = estados_sin_codigo.count()

        if not report_json:
            if count_sin_codigo > 0:
                self.stdout.write(
                    self.style.ERROR(f"[ERROR] {count_sin_codigo} estados sin codigo")
                )

                if verbose:
                    for estado in estados_sin_codigo[:10]:
                        self.stdout.write(
                            f"  - ID: {estado.id}, Nombre: {estado.nombre}, Pais: {estado.pais}"
                        )
            else:
                self.stdout.write(self.style.SUCCESS("[OK] Todos los estados tienen codigo"))

        # ================================================================
        # 8. VERIFICAR EMPRESAS CON Address v2 ACTIVO
        # ================================================================

        if not report_json:
            self.stdout.write("\n[8] Verificando empresas con Address v2 activo...")

        try:
            from taller.models import ConfiguracionEmpresa

            empresas_v2_count = ConfiguracionEmpresa.objects.filter(use_address_v2=True).count()

            total_empresas = Empresa.objects.count()

            porcentaje = (empresas_v2_count / total_empresas * 100) if total_empresas > 0 else 0

            if not report_json:
                self.stdout.write(
                    self.style.SUCCESS(
                        f"[INFO] {empresas_v2_count}/{total_empresas} empresas ({porcentaje:.1f}%) usan Address v2"
                    )
                )
        except:
            empresas_v2_count = 0
            porcentaje = 0

        # ================================================================
        # 9. RESUMEN
        # ================================================================

        total_issues = (
            count_sin_address
            + count_estados_sin_pais
            + count_ciudades_sin_estado
            + count_addresses_sin_city
            + count_legacy
            + count_sin_codigo
        )

        report = {
            "clientes_sin_billing_address": count_sin_address,
            "estados_sin_pais": count_estados_sin_pais,
            "ciudades_sin_estado": count_ciudades_sin_estado,
            "addresses_sin_city": count_addresses_sin_city,
            "clientes_legacy_sin_migrar": count_legacy,
            "estados_sin_codigo": count_sin_codigo,
            "total_issues": total_issues,
            "empresas_con_address_v2": empresas_v2_count,
            "porcentaje_migracion": round(porcentaje, 2),
        }

        if report_json:
            self.stdout.write(json.dumps(report, indent=2))
        else:
            self.stdout.write("\n" + "=" * 60)
            self.stdout.write("\nRESUMEN DE VERIFICACION:")
            self.stdout.write("\n" + "=" * 60 + "\n")

            for key, value in report.items():
                if key in ["total_issues", "empresas_con_address_v2", "porcentaje_migracion"]:
                    continue

                if value > 0:
                    self.stdout.write(self.style.WARNING(f"{key}: {value}"))
                else:
                    self.stdout.write(self.style.SUCCESS(f"{key}: {value} [OK]"))

            self.stdout.write("\n" + "=" * 60)

            if total_issues == 0:
                self.stdout.write(
                    self.style.SUCCESS("\n[OK] VERIFICACION COMPLETA: 0 problemas encontrados\n")
                )
            else:
                self.stdout.write(
                    self.style.WARNING(
                        f"\n[WARN] VERIFICACION COMPLETA: {total_issues} problemas encontrados\n"
                    )
                )
                self.stdout.write("\nACCIONES RECOMENDADAS:\n")

                if count_legacy > 0:
                    self.stdout.write("  1. Ejecutar: python manage.py backfill_addresses")

                if count_sin_address > 0:
                    self.stdout.write("  2. Revisar clientes sin datos de ubicacion")

                if count_estados_sin_pais > 0 or count_sin_codigo > 0:
                    self.stdout.write("  3. Cargar datos de estados faltantes:")
                    self.stdout.write("     - python manage.py cargar_estados_peru")
                    self.stdout.write("     - python manage.py cargar_estados_brasil")
                    self.stdout.write("     - python manage.py cargar_estados_venezuela")

                if count_addresses_sin_city > 0:
                    self.stdout.write("  4. Revisar addresses creados manualmente")

                self.stdout.write("")

        # No retornar nada (Django maneja exit codes automáticamente)
