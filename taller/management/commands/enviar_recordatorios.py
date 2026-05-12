"""
Comando para enviar recordatorios de vencimiento de suscripciones

Uso:
    python manage.py enviar_recordatorios

Configurar en cron para ejecutar diariamente:
    0 9 * * * cd /path/to/egarage && python manage.py enviar_recordatorios
"""

from datetime import timedelta

from django.conf import settings
from django.core.management.base import BaseCommand
from django.template.loader import render_to_string
from django.utils import timezone

from taller.models.empresa import Empresa
from taller.utils.email_helper import get_branded_from_email, send_email_with_reply_to


class Command(BaseCommand):
    help = "Envía recordatorios de vencimiento de suscripciones"

    def add_arguments(self, parser):
        parser.add_argument(
            "--dias",
            type=int,
            default=7,
            help="Días antes del vencimiento para enviar recordatorio (default: 7)",
        )

        parser.add_argument("--dry-run", action="store_true", help="Simular sin enviar emails")

    def handle(self, *args, **options):
        dias_adelanto = options["dias"]
        dry_run = options["dry_run"]

        self.stdout.write(f"🔍 Buscando suscripciones que vencen en {dias_adelanto} días...")

        # Fecha objetivo (ej: dentro de 7 días)
        fecha_objetivo = timezone.now() + timedelta(days=dias_adelanto)
        fecha_inicio = fecha_objetivo.replace(hour=0, minute=0, second=0)
        fecha_fin = fecha_objetivo.replace(hour=23, minute=59, second=59)

        # Buscar empresas con suscripción activa que vence en X días
        empresas = Empresa.objects.filter(
            suscripcion_activa=True,
            fecha_fin__gte=fecha_inicio,
            fecha_fin__lte=fecha_fin,
        )

        total = empresas.count()
        self.stdout.write(f"📊 Encontradas {total} empresas")

        if total == 0:
            self.stdout.write(self.style.SUCCESS("✅ No hay recordatorios para enviar hoy"))
            return

        enviados = 0
        errores = 0

        for empresa in empresas:
            try:
                dias_restantes = (empresa.fecha_fin - timezone.now()).days

                # Determinar idioma
                language = "es" if empresa.pais == "CL" else "en"

                # Renderizar email
                html_message = render_to_string(
                    "emails/vencimiento_proximo.html",
                    {
                        "empresa": empresa,
                        "plan": empresa.plan,
                        "fecha_fin": empresa.fecha_fin,
                        "dias_restantes": dias_restantes,
                        "language": language,
                    },
                )

                # Asunto según idioma
                if language == "en":
                    subject = f"⏰ Your subscription expires in {dias_restantes} days - eGarage"
                else:
                    subject = f"⏰ Tu suscripción vence en {dias_restantes} días - eGarage"

                if dry_run:
                    self.stdout.write(
                        f"[DRY-RUN] Enviaría email a: {empresa.email} ({empresa.nombre_taller})"
                    )
                else:
                    # Enviar email
                    send_email_with_reply_to(
                        subject=subject,
                        message="",
                        from_email=get_branded_from_email(settings.DEFAULT_FROM_EMAIL),
                        recipient_list=[empresa.email],
                        html_message=html_message,
                        fail_silently=False,
                    )

                    self.stdout.write(
                        self.style.SUCCESS(
                            f"✅ Email enviado a: {empresa.email} ({empresa.nombre_taller})"
                        )
                    )

                enviados += 1

            except Exception as e:
                self.stdout.write(self.style.ERROR(f"❌ Error con {empresa.email}: {str(e)}"))
                errores += 1

        # Resumen
        self.stdout.write("\n" + "=" * 60)
        self.stdout.write("📊 RESUMEN:")
        self.stdout.write(f"   Total encontradas: {total}")
        self.stdout.write(f"   ✅ Enviados: {enviados}")
        self.stdout.write(f"   ❌ Errores: {errores}")

        if dry_run:
            self.stdout.write(self.style.WARNING("\n⚠️  Modo DRY-RUN: No se enviaron emails reales"))
        else:
            self.stdout.write(self.style.SUCCESS("\n✅ Recordatorios enviados exitosamente"))
