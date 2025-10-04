"""
Management command para verificar y corregir inconsistencias en datos Cliente ↔ Vehículo ↔ Empresa

Uso:
    python manage.py fix_data_consistency --check    # Solo verificar
    python manage.py fix_data_consistency --fix      # Verificar y corregir
    python manage.py fix_data_consistency --dry-run  # Simular correcciones sin aplicar
"""

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.db.models import F

from taller.models.clientes import Cliente
from taller.models.vehiculos import Vehiculo
from taller.models.documento import Documento
from taller.models.empresa import Empresa


class Command(BaseCommand):
    help = 'Verificar y corregir inconsistencias en datos Cliente ↔ Vehículo ↔ Empresa'

    def add_arguments(self, parser):
        parser.add_argument(
            '--check',
            action='store_true',
            help='Solo verificar inconsistencias',
        )
        parser.add_argument(
            '--fix',
            action='store_true',
            help='Verificar y corregir inconsistencias',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Simular correcciones sin aplicar',
        )

    def handle(self, *args, **options):
        check_only = options['check']
        fix_data = options['fix']
        dry_run = options['dry_run']

        if not any([check_only, fix_data, dry_run]):
            raise CommandError('Debe especificar --check, --fix o --dry-run')

        # Siempre verificar primero
        issues = self.check_inconsistencies()

        # Aplicar correcciones si se solicita
        if fix_data or dry_run:
            if issues:
                self.stdout.write(
                    self.style.WARNING(
                        f"\n⚠️  {'SIMULANDO' if dry_run else 'APLICANDO'} CORRECCIONES..."
                    )
                )
                fixed_count = self.fix_inconsistencies(dry_run=dry_run)

                if dry_run:
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"\n💡 Para aplicar las correcciones, ejecuta: python manage.py fix_data_consistency --fix"
                        )
                    )
                else:
                    self.stdout.write(
                        self.style.SUCCESS(f"\n✅ Correcciones aplicadas exitosamente")
                    )
            else:
                self.stdout.write(
                    self.style.SUCCESS(f"\n✅ No hay correcciones necesarias")
                )

    def check_inconsistencies(self):
        """Verifica inconsistencias en los datos"""
        self.stdout.write("🔍 VERIFICANDO INCONSISTENCIAS EN DATOS...")
        self.stdout.write("=" * 60)

        issues = []

        # 1. Vehículos sin empresa
        vehiculos_sin_empresa = Vehiculo.objects.filter(empresa__isnull=True)
        if vehiculos_sin_empresa.exists():
            count = vehiculos_sin_empresa.count()
            issues.append(f"❌ {count} vehículos sin empresa asignada")
            self.stdout.write(f"   Vehículos sin empresa: {count}")

            # Mostrar algunos ejemplos
            for v in vehiculos_sin_empresa[:5]:
                self.stdout.write(
                    f"     - Vehículo ID {v.id}: {v.patente} (Cliente: {v.cliente})"
                )

        # 2. Vehículos con empresa diferente a la del cliente
        vehiculos_empresa_inconsistente = Vehiculo.objects.exclude(
            empresa=F('cliente__empresa')
        )
        if vehiculos_empresa_inconsistente.exists():
            count = vehiculos_empresa_inconsistente.count()
            issues.append(f"❌ {count} vehículos con empresa diferente a la del cliente")
            self.stdout.write(f"   Vehículos con empresa inconsistente: {count}")

            # Mostrar algunos ejemplos
            for v in vehiculos_empresa_inconsistente[:5]:
                self.stdout.write(f"     - Vehículo ID {v.id}: {v.patente}")
                self.stdout.write(f"       Vehículo empresa: {v.empresa}")
                self.stdout.write(
                    f"       Cliente empresa: {v.cliente.empresa if v.cliente else 'N/A'}"
                )

        # 3. Clientes sin empresa
        clientes_sin_empresa = Cliente.objects.filter(empresa__isnull=True)
        if clientes_sin_empresa.exists():
            count = clientes_sin_empresa.count()
            issues.append(f"❌ {count} clientes sin empresa asignada")
            self.stdout.write(f"   Clientes sin empresa: {count}")

            # Mostrar algunos ejemplos
            for c in clientes_sin_empresa[:5]:
                self.stdout.write(
                    f"     - Cliente ID {c.id}: {c.nombre} {c.apellido}"
                )

        # 4. Documentos con inconsistencias
        documentos_problematicos = []
        for doc in Documento.objects.select_related('cliente', 'vehiculo', 'empresa'):
            has_issue = False

            # Cliente no pertenece a la empresa del documento
            if doc.cliente and doc.empresa and doc.cliente.empresa != doc.empresa:
                has_issue = True

            # Vehículo no pertenece a la empresa del documento
            if doc.vehiculo and doc.empresa and doc.vehiculo.empresa != doc.empresa:
                has_issue = True

            # Vehículo no pertenece al cliente del documento
            if doc.vehiculo and doc.cliente and doc.vehiculo.cliente != doc.cliente:
                has_issue = True

            if has_issue:
                documentos_problematicos.append(doc)

        if documentos_problematicos:
            issues.append(
                f"❌ {len(documentos_problematicos)} documentos con inconsistencias"
            )
            self.stdout.write(f"   Documentos problemáticos: {len(documentos_problematicos)}")

            # Mostrar algunos ejemplos
            for doc in documentos_problematicos[:3]:
                self.stdout.write(
                    f"     - Documento ID {doc.id}: {doc.tipo} #{doc.numero}"
                )
                self.stdout.write(f"       Empresa doc: {doc.empresa}")
                self.stdout.write(
                    f"       Cliente: {doc.cliente} (empresa: {doc.cliente.empresa if doc.cliente else 'N/A'})"
                )
                self.stdout.write(
                    f"       Vehículo: {doc.vehiculo} (empresa: {doc.vehiculo.empresa if doc.vehiculo else 'N/A'})"
                )

        # Resumen
        self.stdout.write("\n" + "=" * 60)
        if issues:
            self.stdout.write(
                self.style.ERROR(f"🚨 ENCONTRADAS {len(issues)} INCONSISTENCIAS:")
            )
            for issue in issues:
                self.stdout.write(f"   {issue}")
        else:
            self.stdout.write(
                self.style.SUCCESS("✅ NO SE ENCONTRARON INCONSISTENCIAS")
            )

        return issues

    @transaction.atomic
    def fix_inconsistencies(self, dry_run=False):
        """Corrige las inconsistencias encontradas"""
        self.stdout.write(
            f"\n🔧 {'SIMULANDO' if dry_run else 'APLICANDO'} CORRECCIONES..."
        )
        self.stdout.write("=" * 60)

        fixed_count = 0

        # 1. Asignar empresa a vehículos sin empresa (basado en el cliente)
        vehiculos_sin_empresa = Vehiculo.objects.filter(empresa__isnull=True)
        for v in vehiculos_sin_empresa:
            if v.cliente and v.cliente.empresa:
                if not dry_run:
                    v.empresa = v.cliente.empresa
                    v.save()
                self.stdout.write(
                    f"   ✅ Vehículo {v.id} ({v.patente}): empresa = {v.cliente.empresa}"
                )
                fixed_count += 1

        # 2. Corregir vehículos con empresa inconsistente
        vehiculos_empresa_inconsistente = Vehiculo.objects.exclude(
            empresa=F('cliente__empresa')
        )
        for v in vehiculos_empresa_inconsistente:
            if v.cliente and v.cliente.empresa:
                old_empresa = v.empresa
                if not dry_run:
                    v.empresa = v.cliente.empresa
                    v.save()
                self.stdout.write(
                    f"   ✅ Vehículo {v.id} ({v.patente}): {old_empresa} → {v.cliente.empresa}"
                )
                fixed_count += 1

        # 3. Asignar empresa a clientes sin empresa (basado en los vehículos)
        clientes_sin_empresa = Cliente.objects.filter(empresa__isnull=True)
        for c in clientes_sin_empresa:
            # Buscar la empresa más común entre los vehículos del cliente
            vehiculos_empresas = (
                Vehiculo.objects.filter(cliente=c, empresa__isnull=False)
                .values_list('empresa', flat=True)
                .distinct()
            )
            if vehiculos_empresas:
                # Usar la primera empresa encontrada
                empresa_comun = vehiculos_empresas[0]
                if not dry_run:
                    c.empresa_id = empresa_comun
                    c.save()
                self.stdout.write(
                    f"   ✅ Cliente {c.id} ({c.nombre} {c.apellido}): empresa = {empresa_comun}"
                )
                fixed_count += 1

        self.stdout.write(
            f"\n📊 TOTAL CORRECCIONES {'SIMULADAS' if dry_run else 'APLICADAS'}: {fixed_count}"
        )

        return fixed_count
