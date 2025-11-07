"""
Comando para verificar y desactivar suscripciones vencidas

Uso:
    python manage.py verificar_suscripciones

Configurar en cron para ejecutar diariamente:
    0 1 * * * cd /path/to/egarage && python manage.py verificar_suscripciones
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings

from taller.models.empresa import Empresa


class Command(BaseCommand):
    help = 'Verifica y desactiva suscripciones vencidas'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Simular sin desactivar suscripciones'
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        self.stdout.write("🔍 Buscando suscripciones vencidas...")
        
        # Buscar empresas con suscripción activa pero fecha_fin pasada
        empresas_vencidas = Empresa.objects.filter(
            suscripcion_activa=True,
            fecha_fin__lt=timezone.now(),
        )
        
        total = empresas_vencidas.count()
        self.stdout.write(f"📊 Encontradas {total} suscripciones vencidas")
        
        if total == 0:
            self.stdout.write(self.style.SUCCESS("✅ No hay suscripciones vencidas"))
            return
        
        desactivadas = 0
        errores = 0
        
        for empresa in empresas_vencidas:
            try:
                if dry_run:
                    self.stdout.write(f"[DRY-RUN] Desactivaría: {empresa.nombre_taller} (vencido: {empresa.fecha_fin})")
                else:
                    # Desactivar suscripción
                    empresa.suscripcion_activa = False
                    empresa.save(update_fields=['suscripcion_activa'])
                    
                    # Enviar email de notificación
                    language = 'es' if empresa.pais == 'CL' else 'en'
                    
                    html_message = render_to_string('email/suscripcion_vencida.html', {
                        'empresa': empresa,
                        'plan': empresa.plan,
                        'fecha_fin': empresa.fecha_fin,
                        'language': language,
                    })
                    
                    if language == 'en':
                        subject = '⚠️ Your subscription has expired - eGarage'
                    else:
                        subject = '⚠️ Tu suscripción ha vencido - eGarage'
                    
                    send_mail(
                        subject=subject,
                        message='',
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        recipient_list=[empresa.email],
                        html_message=html_message,
                        fail_silently=True,
                    )
                    
                    self.stdout.write(self.style.WARNING(f"⚠️ Desactivada: {empresa.nombre_taller}"))
                
                desactivadas += 1
                
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"❌ Error con {empresa.nombre_taller}: {str(e)}"))
                errores += 1
        
        # Resumen
        self.stdout.write("\n" + "="*60)
        self.stdout.write(f"📊 RESUMEN:")
        self.stdout.write(f"   Total vencidas: {total}")
        self.stdout.write(f"   ⚠️  Desactivadas: {desactivadas}")
        self.stdout.write(f"   ❌ Errores: {errores}")
        
        if dry_run:
            self.stdout.write(self.style.WARNING("\n⚠️  Modo DRY-RUN: No se desactivaron suscripciones"))
        else:
            self.stdout.write(self.style.SUCCESS("\n✅ Verificación completada"))

