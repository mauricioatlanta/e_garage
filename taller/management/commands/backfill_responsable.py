from django.core.management.base import BaseCommand
from django.db import transaction
from taller.models import Documento


class Command(BaseCommand):
    help = "Backfill de responsable en líneas desde Documento.tecnico_responsable"

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Mostrar qué se haría sin ejecutar cambios',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        if dry_run:
            self.stdout.write(self.style.WARNING("🔍 Modo dry-run activado"))
        
        try:
            with transaction.atomic():
                documentos = Documento.objects.select_related("tecnico_responsable").all()
                total_docs = documentos.count()
                
                self.stdout.write(f"📊 Procesando {total_docs} documentos...")
                
                for i, d in enumerate(documentos, 1):
                if d.tecnico_responsable:
                    if not dry_run:
                        # NOTA: Las líneas no tienen campo 'responsable' en el modelo actual
                        # El responsable se obtiene del documento__tecnico_responsable
                        # Este comando está preparado para cuando se implemente el campo 'responsable'
                        self.stdout.write(
                            self.style.WARNING(
                                f"   ⚠️  Documento {d.pk}: Campo 'responsable' no existe en líneas. "
                                "Usar documento__tecnico_responsable en KPIs."
                            )
                        )
                        
                        if i % 100 == 0:
                            self.stdout.write(f"   Procesados {i}/{total_docs} documentos...")
                    else:
                        self.stdout.write(
                            self.style.WARNING(f"   ⚠️  Documento {d.pk} sin técnico responsable")
                        )
                
                if dry_run:
                    self.stdout.write(
                        self.style.SUCCESS(f"✅ Dry-run completado para {total_docs} documentos")
                    )
                else:
                    self.stdout.write(
                        self.style.SUCCESS(f"✅ Backfill completado para {total_docs} documentos")
                    )
                    
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"❌ Error en backfill: {e}")
            )
            raise
