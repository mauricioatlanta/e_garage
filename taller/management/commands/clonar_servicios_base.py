"""
Comando de Django para clonar servicios base de una empresa maestra
a todas las demás empresas del sistema.

Uso:
    python manage.py clonar_servicios_base
    python manage.py clonar_servicios_base --empresa-maestra 1
    python manage.py clonar_servicios_base --forzar
"""

from django.core.management.base import BaseCommand
from django.db import transaction

from taller.models import Empresa
from taller.servicios.models import Servicio, ServicioName


class Command(BaseCommand):
    help = 'Clona servicios de una empresa maestra a todas las demás empresas'

    def add_arguments(self, parser):
        parser.add_argument(
            '--empresa-maestra',
            type=int,
            default=1,
            help='ID de la empresa maestra (default: 1)'
        )
        parser.add_argument(
            '--forzar',
            action='store_true',
            help='Forzar actualización de servicios existentes'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Simular sin hacer cambios reales'
        )

    def handle(self, *args, **options):
        empresa_maestra_id = options['empresa_maestra']
        forzar = options['forzar']
        dry_run = options['dry_run']
        
        if dry_run:
            self.stdout.write(self.style.WARNING('🔍 MODO DRY-RUN: No se harán cambios reales\n'))
        
        self.stdout.write("🚀 Iniciando clonación de servicios base...")
        self.stdout.write(f"   Empresa maestra ID: {empresa_maestra_id}")
        self.stdout.write(f"   Modo forzar: {'Sí' if forzar else 'No'}")
        self.stdout.write("")
        
        try:
            # 1. Definir la empresa origen
            try:
                maestra = Empresa.objects.get(id=empresa_maestra_id)
                self.stdout.write(
                    self.style.SUCCESS(
                        f"✅ Empresa maestra encontrada: {maestra.nombre_taller} (ID: {maestra.id})"
                    )
                )
            except Empresa.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(
                        f"❌ Error: No existe una empresa con ID={empresa_maestra_id} para usar de plantilla."
                    )
                )
                return

            servicios_maestros = Servicio.objects.filter(empresa=maestra)
            total_servicios = servicios_maestros.count()
            
            if total_servicios == 0:
                self.stdout.write(
                    self.style.WARNING(
                        "⚠️  Advertencia: La empresa maestra no tiene servicios para clonar."
                    )
                )
                return
            
            self.stdout.write(f"📦 Servicios maestros encontrados: {total_servicios}")
            
            todas_las_empresas = Empresa.objects.exclude(id=empresa_maestra_id)
            total_empresas = todas_las_empresas.count()
            
            if total_empresas == 0:
                self.stdout.write(
                    self.style.WARNING("⚠️  No hay otras empresas para clonar servicios.")
                )
                return
            
            self.stdout.write(f"🏢 Empresas a procesar: {total_empresas}\n")
            self.stdout.write("=" * 60)

            servicios_creados = 0
            servicios_actualizados = 0
            nombres_clonados = 0

            with transaction.atomic():
                for empresa in todas_las_empresas:
                    self.stdout.write(
                        f"\n📋 Verificando servicios para: {empresa.nombre_taller} (ID: {empresa.id})..."
                    )
                    
                    for s_maestro in servicios_maestros:
                        # Verificar si el servicio ya existe para esta empresa
                        servicio_existente = Servicio.objects.filter(
                            empresa=empresa,
                            nombre=s_maestro.nombre,
                            categoria=s_maestro.categoria
                        ).first()
                        
                        if servicio_existente:
                            if forzar:
                                if not dry_run:
                                    # Actualizar servicio existente
                                    servicio_existente.subcategoria = s_maestro.subcategoria
                                    servicio_existente.save()
                                servicios_actualizados += 1
                                self.stdout.write(
                                    f"   🔄 {'[DRY-RUN] ' if dry_run else ''}Actualizado: {s_maestro.nombre}"
                                )
                            else:
                                self.stdout.write(
                                    f"   ⏭️  Ya existe: {s_maestro.nombre} (omitido)"
                                )
                                continue
                        else:
                            if not dry_run:
                                # Crear el servicio para la empresa actual
                                nuevo_servicio = Servicio.objects.create(
                                    empresa=empresa,
                                    nombre=s_maestro.nombre,
                                    categoria=s_maestro.categoria,
                                    subcategoria=s_maestro.subcategoria
                                )
                            else:
                                # En dry-run, crear un objeto ficticio para la lógica
                                nuevo_servicio = None
                            servicios_creados += 1
                            self.stdout.write(
                                f"   ✅ {'[DRY-RUN] ' if dry_run else ''}Creado: {s_maestro.nombre}"
                            )

                        # Clonar también las traducciones/nombres localizados
                        servicio_objetivo = servicio_existente if servicio_existente else nuevo_servicio
                        
                        if servicio_objetivo:
                            # Eliminar nombres existentes si estamos forzando
                            if forzar and servicio_existente and not dry_run:
                                ServicioName.objects.filter(servicio=servicio_objetivo).delete()
                            
                            # Clonar nombres localizados
                            nombres_maestros = ServicioName.objects.filter(servicio=s_maestro)
                            for n in nombres_maestros:
                                # Verificar si ya existe este nombre para evitar duplicados
                                nombre_existente = ServicioName.objects.filter(
                                    servicio=servicio_objetivo,
                                    language=n.language,
                                    is_default=n.is_default
                                ).first()
                                
                                if not nombre_existente:
                                    if not dry_run:
                                        ServicioName.objects.create(
                                            servicio=servicio_objetivo,
                                            language=n.language,
                                            label=n.label,
                                            aliases=n.aliases.copy() if n.aliases else [],
                                            is_default=n.is_default
                                        )
                                    nombres_clonados += 1
                    
                    self.stdout.write(
                        self.style.SUCCESS(f"   ✅ Empresa {empresa.id} sincronizada.")
                    )
                
                if dry_run:
                    # En dry-run, no hacemos commit
                    transaction.set_rollback(True)
                    self.stdout.write(
                        self.style.WARNING("\n🔍 DRY-RUN: Cambios simulados, no se guardaron.")
                    )

            self.stdout.write("\n" + "=" * 60)
            self.stdout.write("📊 RESUMEN:")
            self.stdout.write(f"   • Servicios creados: {servicios_creados}")
            self.stdout.write(f"   • Servicios actualizados: {servicios_actualizados}")
            self.stdout.write(f"   • Nombres localizados clonados: {nombres_clonados}")
            self.stdout.write(f"   • Total empresas procesadas: {total_empresas}")
            self.stdout.write("=" * 60)
            
            if not dry_run:
                self.stdout.write(
                    self.style.SUCCESS("\n✅ Proceso completado exitosamente!")
                )
            else:
                self.stdout.write(
                    self.style.WARNING("\n🔍 Ejecuta sin --dry-run para aplicar los cambios.")
                )
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"\n❌ Error durante la ejecución: {e}")
            )
            import traceback
            traceback.print_exc()
            raise

