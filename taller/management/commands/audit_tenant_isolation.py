"""
Management command para auditar y corregir el aislamiento multi-tenant

Uso:
python manage.py audit_tenant_isolation --dry-run
python manage.py audit_tenant_isolation --fix
"""

import logging

from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import F, Q
from django.utils import timezone

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Audita y corrige datos mezclados entre empresas"

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run", action="store_true", help="Solo mostrar problemas sin corregir"
        )
        parser.add_argument(
            "--fix",
            action="store_true",
            help="Corregir problemas automáticamente cuando sea posible",
        )
        parser.add_argument(
            "--verbose", action="store_true", help="Mostrar información detallada"
        )

    def handle(self, *args, **options):
        self.dry_run = options["dry_run"]
        self.fix_mode = options["fix"]
        self.verbose = options["verbose"]

        if not self.dry_run and not self.fix_mode:
            self.stdout.write(
                self.style.WARNING(
                    "Especifica --dry-run para ver problemas o --fix para corregir"
                )
            )
            return

        self.stdout.write(
            self.style.SUCCESS(
                f'=== AUDITORÍA MULTI-TENANT {"(MODO CORRECCIÓN)" if self.fix_mode else "(MODO SOLO LECTURA)"} ==='
            )
        )

        try:
            # Importar modelos
            from taller.documentos.models import Documento
            from taller.models.clientes import Cliente
            from taller.models.repuesto import Repuesto
            from taller.models.vehiculos import Vehiculo
            from taller.servicios.models import Servicio

            # Auditar cada modelo
            self.audit_clientes(Cliente)
            self.audit_vehiculos(Vehiculo)
            self.audit_documentos(Documento)
            self.audit_repuestos(Repuesto)
            self.audit_servicios(Servicio)

            # Auditar líneas de documento
            self.audit_lineas_documento()

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error durante auditoría: {e}"))
            raise

        self.stdout.write(self.style.SUCCESS("=== AUDITORÍA COMPLETADA ==="))

    def audit_clientes(self, Cliente):
        """Auditar clientes sin empresa o con datos inconsistentes"""
        self.stdout.write("\n--- AUDITANDO CLIENTES ---")

        # Clientes sin empresa
        bad_clientes = Cliente.objects.filter(empresa__isnull=True)
        count = bad_clientes.count()

        if count > 0:
            self.stdout.write(
                self.style.ERROR(f"❌ {count} clientes sin empresa asignada")
            )

            if self.verbose:
                for cliente in bad_clientes[:10]:  # Mostrar solo primeros 10
                    self.stdout.write(
                        f"  - Cliente ID: {cliente.pk}, Nombre: {cliente.nombre}"
                    )

            if self.fix_mode:
                self.stdout.write(
                    self.style.WARNING(
                        "❌ No se puede inferir empresa para clientes huérfanos"
                    )
                )
        else:
            self.stdout.write(
                self.style.SUCCESS("✅ Todos los clientes tienen empresa")
            )

        # Clientes con emails duplicados entre empresas
        from django.db.models import Count

        duplicated_emails = (
            Cliente.objects.filter(email__isnull=False)
            .exclude(email="")
            .values("email")
            .annotate(count=Count("id"), empresas=Count("empresa", distinct=True))
            .filter(empresas__gt=1)
        )

        if duplicated_emails.exists():
            self.stdout.write(
                self.style.WARNING(
                    f"⚠️ {duplicated_emails.count()} emails compartidos entre empresas"
                )
            )
            if self.verbose:
                for item in duplicated_emails[:5]:
                    clientes = Cliente.objects.filter(email=item["email"])
                    self.stdout.write(f'  - Email: {item["email"]}')
                    for c in clientes:
                        self.stdout.write(
                            f'    * Empresa: {c.empresa.nombre if c.empresa else "SIN EMPRESA"}'
                        )

    def audit_vehiculos(self, Vehiculo):
        """Auditar vehículos con empresas inconsistentes"""
        self.stdout.write("\n--- AUDITANDO VEHÍCULOS ---")

        # Vehículos sin empresa
        bad_vehiculos = Vehiculo.objects.filter(empresa__isnull=True)
        count = bad_vehiculos.count()

        if count > 0:
            self.stdout.write(self.style.ERROR(f"❌ {count} vehículos sin empresa"))

            if self.fix_mode:
                fixed = 0
                with transaction.atomic():
                    for vehiculo in bad_vehiculos:
                        if vehiculo.cliente and vehiculo.cliente.empresa:
                            vehiculo.empresa = vehiculo.cliente.empresa
                            vehiculo.save()
                            fixed += 1
                            if self.verbose:
                                self.stdout.write(
                                    f"  ✅ Corregido vehículo {vehiculo.pk} -> empresa {vehiculo.empresa.nombre}"
                                )

                self.stdout.write(
                    self.style.SUCCESS(f"✅ Corregidos {fixed} vehículos")
                )
        else:
            self.stdout.write(
                self.style.SUCCESS("✅ Todos los vehículos tienen empresa")
            )

        # Vehículos con empresa diferente a su cliente
        inconsistent_vehiculos = Vehiculo.objects.filter(
            ~Q(empresa=F("cliente__empresa"))
        ).exclude(cliente__empresa__isnull=True)

        count = inconsistent_vehiculos.count()
        if count > 0:
            self.stdout.write(
                self.style.ERROR(
                    f"❌ {count} vehículos con empresa inconsistente con su cliente"
                )
            )

            if self.fix_mode:
                fixed = 0
                with transaction.atomic():
                    for vehiculo in inconsistent_vehiculos:
                        vehiculo.empresa = vehiculo.cliente.empresa
                        vehiculo.save()
                        fixed += 1
                        if self.verbose:
                            self.stdout.write(f"  ✅ Corregido vehículo {vehiculo.pk}")

                self.stdout.write(
                    self.style.SUCCESS(
                        f"✅ Corregidos {fixed} vehículos inconsistentes"
                    )
                )
        else:
            self.stdout.write(
                self.style.SUCCESS("✅ Todos los vehículos tienen empresa consistente")
            )

    def audit_documentos(self, Documento):
        """Auditar documentos con empresas inconsistentes"""
        self.stdout.write("\n--- AUDITANDO DOCUMENTOS ---")

        # Documentos sin empresa
        bad_documentos = Documento.objects.filter(empresa__isnull=True)
        count = bad_documentos.count()

        if count > 0:
            self.stdout.write(self.style.ERROR(f"❌ {count} documentos sin empresa"))

            if self.fix_mode:
                fixed = 0
                with transaction.atomic():
                    for documento in bad_documentos:
                        if documento.cliente and documento.cliente.empresa:
                            documento.empresa = documento.cliente.empresa
                            documento.save()
                            fixed += 1
                        elif documento.vehiculo and documento.vehiculo.empresa:
                            documento.empresa = documento.vehiculo.empresa
                            documento.save()
                            fixed += 1

                self.stdout.write(
                    self.style.SUCCESS(f"✅ Corregidos {fixed} documentos")
                )
        else:
            self.stdout.write(
                self.style.SUCCESS("✅ Todos los documentos tienen empresa")
            )

        # Documentos con empresas inconsistentes
        inconsistent_docs = Documento.objects.filter(
            Q(cliente__isnull=False) & ~Q(empresa=F("cliente__empresa"))
        )

        count = inconsistent_docs.count()
        if count > 0:
            self.stdout.write(
                self.style.ERROR(
                    f"❌ {count} documentos con empresa inconsistente con cliente"
                )
            )

            if self.fix_mode:
                fixed = 0
                with transaction.atomic():
                    for documento in inconsistent_docs:
                        documento.empresa = documento.cliente.empresa
                        documento.save()
                        fixed += 1

                self.stdout.write(
                    self.style.SUCCESS(
                        f"✅ Corregidos {fixed} documentos inconsistentes"
                    )
                )

    def audit_repuestos(self, Repuesto):
        """Auditar repuestos"""
        self.stdout.write("\n--- AUDITANDO REPUESTOS ---")

        if hasattr(Repuesto, "empresa"):
            bad_repuestos = Repuesto.objects.filter(empresa__isnull=True)
            count = bad_repuestos.count()

            if count > 0:
                self.stdout.write(self.style.ERROR(f"❌ {count} repuestos sin empresa"))
            else:
                self.stdout.write(
                    self.style.SUCCESS("✅ Todos los repuestos tienen empresa")
                )
        else:
            self.stdout.write(
                self.style.WARNING("⚠️ Modelo Repuesto no es multi-tenant")
            )

    def audit_servicios(self, Servicio):
        """Auditar servicios"""
        self.stdout.write("\n--- AUDITANDO SERVICIOS ---")

        if hasattr(Servicio, "empresa"):
            bad_servicios = Servicio.objects.filter(empresa__isnull=True)
            count = bad_servicios.count()

            if count > 0:
                self.stdout.write(self.style.ERROR(f"❌ {count} servicios sin empresa"))
            else:
                self.stdout.write(
                    self.style.SUCCESS("✅ Todos los servicios tienen empresa")
                )
        else:
            self.stdout.write(
                self.style.WARNING("⚠️ Modelo Servicio no es multi-tenant")
            )

    def audit_lineas_documento(self):
        """Auditar líneas de documentos"""
        self.stdout.write("\n--- AUDITANDO LÍNEAS DE DOCUMENTO ---")

        try:
            from taller.documentos.models import (LineaOtroServicio,
                                                  LineaRepuesto, LineaServicio)

            # Auditar LineaRepuesto
            if hasattr(LineaRepuesto, "empresa"):
                bad_lineas = LineaRepuesto.objects.filter(
                    ~Q(empresa=F("documento__empresa"))
                )
                count = bad_lineas.count()

                if count > 0:
                    self.stdout.write(
                        self.style.ERROR(
                            f"❌ {count} líneas de repuesto con empresa inconsistente"
                        )
                    )

                    if self.fix_mode:
                        fixed = 0
                        with transaction.atomic():
                            for linea in bad_lineas:
                                linea.empresa = linea.documento.empresa
                                linea.save()
                                fixed += 1

                        self.stdout.write(
                            self.style.SUCCESS(
                                f"✅ Corregidas {fixed} líneas de repuesto"
                            )
                        )
                else:
                    self.stdout.write(
                        self.style.SUCCESS("✅ Líneas de repuesto consistentes")
                    )

            # Auditar LineaServicio
            if hasattr(LineaServicio, "empresa"):
                bad_lineas = LineaServicio.objects.filter(
                    ~Q(empresa=F("documento__empresa"))
                )
                count = bad_lineas.count()

                if count > 0:
                    self.stdout.write(
                        self.style.ERROR(
                            f"❌ {count} líneas de servicio con empresa inconsistente"
                        )
                    )

                    if self.fix_mode:
                        fixed = 0
                        with transaction.atomic():
                            for linea in bad_lineas:
                                linea.empresa = linea.documento.empresa
                                linea.save()
                                fixed += 1

                        self.stdout.write(
                            self.style.SUCCESS(
                                f"✅ Corregidas {fixed} líneas de servicio"
                            )
                        )
                else:
                    self.stdout.write(
                        self.style.SUCCESS("✅ Líneas de servicio consistentes")
                    )

        except ImportError:
            self.stdout.write(
                self.style.WARNING("⚠️ No se pudieron importar modelos de líneas")
            )
