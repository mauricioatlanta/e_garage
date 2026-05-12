from datetime import timedelta

from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils import timezone

from taller.models.empresa import Empresa
from taller.models.suscripcion import Suscripcion
from taller.utils.email_helper import get_support_reply_to, send_email_with_reply_to
from taller.utils.payment_config import build_transfer_payment_message


class Command(BaseCommand):
    """
    Comando para enviar notificaciones de vencimiento de suscripción.

    Intervalos de notificación:
    - 7 días antes: Usa campo notificacion_5_dias (reutilizado para "aviso temprano")
    - 3 días antes: Usa campo notificacion_5_dias (mismo campo, evita duplicados)
    - 1 día antes: Usa campo notificacion_1_dia (campo específico)
    - Vencidas (hoy): Usa campo notificacion_vencido (campo específico)

    NOTA IMPORTANTE: El campo notificacion_5_dias se reutiliza para 7 y 3 días porque
    el modelo solo tiene 3 campos booleanos. Esta es una decisión de diseño para evitar
    múltiples campos similares. Si se necesita separar, considerar agregar campos específicos.

    Optimización de rendimiento:
    - Usa select_related("user") para evitar N+1 queries cuando se accede a empresa.user
    - Filtra empresas activas antes de procesar

    Uso:
        python manage.py notificar_vencimientos          # Ejecución normal
        python manage.py notificar_vencimientos --dry-run  # Modo prueba (no envía ni marca)

    Ejecutar diariamente con cron:
        0 9 * * * cd /ruta/proyecto && python manage.py notificar_vencimientos
    """

    help = "Envía notificaciones de vencimiento de suscripción (7, 3, 1 día y vencidas)"

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Ejecutar en modo de prueba sin enviar emails ni marcar notificaciones",
        )

    def handle(self, *args, **options):
        dry_run = options.get("dry_run", False)

        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    "[DRY-RUN] Modo de prueba: No se enviaran emails ni se marcaran notificaciones"
                )
            )

        self.stdout.write("[INFO] Iniciando verificacion de suscripciones...")

        hoy = timezone.now()

        # Optimización: usar select_related para evitar N+1 queries
        base_query = Empresa.objects.filter(suscripcion_activa=True).select_related("user")

        # Empresas que vencen en 7 días
        # NOTA: Reutilizamos notificacion_5_dias para 7 y 3 días (campo genérico para "aviso temprano")
        empresas_7_dias = base_query.filter(
            fecha_fin__date=hoy.date() + timedelta(days=7),
            notificacion_5_dias=False,  # Anti-duplicado: campo usado para avisos tempranos (7 y 3 días)
        )

        # Empresas que vencen en 3 días (excluyendo las de 7 días para evitar duplicados)
        empresas_3_dias = base_query.filter(
            fecha_fin__date=hoy.date() + timedelta(days=3),
            notificacion_5_dias=False,  # Anti-duplicado: mismo campo que 7 días
        ).exclude(
            id__in=empresas_7_dias.values_list("id", flat=True)  # Evitar duplicados
        )

        # Empresas que vencen mañana (1 día)
        empresas_1_dia = base_query.filter(
            fecha_fin__date=hoy.date() + timedelta(days=1),
            notificacion_1_dia=False,  # Campo específico para 1 día
        )

        # Empresas que vencieron hoy
        empresas_vencidas = base_query.filter(
            fecha_fin__date=hoy.date(),
            notificacion_vencido=False,  # Campo específico para vencidas
        )

        # Enviar notificaciones
        count_7_dias = self.enviar_notificacion(empresas_7_dias, 7, dry_run)
        count_3_dias = self.enviar_notificacion(empresas_3_dias, 3, dry_run)
        count_1_dia = self.enviar_notificacion(empresas_1_dia, 1, dry_run)
        count_vencidas = self.enviar_notificacion_vencido(empresas_vencidas, dry_run)

        self.stdout.write(
            self.style.SUCCESS(
                f"[OK] Notificaciones{' (simuladas)' if dry_run else ''}: "
                f"{count_7_dias} (7 dias), {count_3_dias} (3 dias), "
                f"{count_1_dia} (1 dia), {count_vencidas} (vencidas)"
            )
        )

    def enviar_notificacion(self, empresas, dias_restantes, dry_run=False):
        """
        Envía notificación de vencimiento para empresas que vencen en X días.

        Args:
            empresas: QuerySet de empresas
            dias_restantes: Número de días restantes hasta vencimiento
            dry_run: Si True, solo simula el envío sin enviar ni marcar

        Returns:
            int: Número de notificaciones enviadas/simuladas
        """
        count = 0
        for empresa in empresas:
            try:
                # Anti-duplicado: verificar si ya se envió esta notificación
                # NOTA: notificacion_5_dias se usa para avisos tempranos (7 y 3 días)
                if dias_restantes in [7, 3]:
                    if empresa.notificacion_5_dias:
                        self.stdout.write(
                            self.style.WARNING(
                                f"[SKIP] Omitiendo {empresa.nombre_taller}: ya recibio notificacion temprana ({dias_restantes} dias)"
                            )
                        )
                        continue
                elif dias_restantes == 1:
                    if empresa.notificacion_1_dia:
                        self.stdout.write(
                            self.style.WARNING(
                                f"[SKIP] Omitiendo {empresa.nombre_taller}: ya recibio notificacion de 1 dia"
                            )
                        )
                        continue

                # Obtener variables de soporte centralizadas
                support_email = get_support_reply_to()
                support_whatsapp_wa_me = getattr(settings, "SUPPORT_WHATSAPP_WA_ME", "56953574683")
                support_whatsapp_display = getattr(
                    settings, "SUPPORT_WHATSAPP_DISPLAY", "+56 9 5357 4683"
                )

                subject = f"[IMPORTANTE] Tu suscripcion a eGarage vence en {dias_restantes} dia{'s' if dias_restantes > 1 else ''}"
                fecha_venc = (
                    empresa.fecha_fin.strftime("%d/%m/%Y") if empresa.fecha_fin else "pronto"
                )
                plan_display = (
                    empresa.get_plan_display() if hasattr(empresa, "get_plan_display") else "Activo"
                )
                nombre_usuario = empresa.user.first_name or empresa.user.username

                message = f"""
Hola {nombre_usuario},

Tu suscripción a eGarage para {empresa.nombre_taller} vencerá en {dias_restantes} día{'s' if dias_restantes > 1 else ''}.

Fecha de vencimiento: {fecha_venc}
Plan actual: {plan_display}

Para renovar tu suscripción:
1. Ingresa a tu panel de administración
2. Ve a la sección de pagos
3. Sube tu comprobante de pago

¿Necesitas ayuda?
Email: {support_email}
WhatsApp: {support_whatsapp_display}
Link: https://wa.me/{support_whatsapp_wa_me}?text=Hola,%20tengo%20una%20pregunta%20sobre%20mi%20suscripcion%20eGarage

Equipo eGarage
                """

                if dry_run:
                    self.stdout.write(
                        self.style.WARNING(
                            f"[DRY-RUN] Simulando envio a {empresa.user.email} ({empresa.nombre_taller}) - {dias_restantes} dias restantes"
                        )
                    )
                else:
                    send_email_with_reply_to(
                        subject=subject,
                        message=message,
                        recipient_list=[empresa.user.email],
                        fail_silently=False,
                    )

                    # Marcar como notificado para evitar duplicados
                    # NOTA: notificacion_5_dias se usa para avisos tempranos (7 y 3 días)
                    if dias_restantes in [7, 3]:
                        empresa.notificacion_5_dias = True
                        empresa.save(update_fields=["notificacion_5_dias"])
                    elif dias_restantes == 1:
                        empresa.notificacion_1_dia = True
                        empresa.save(update_fields=["notificacion_1_dia"])

                    self.stdout.write(
                        self.style.SUCCESS(
                            f"[OK] Email enviado a {empresa.user.email} ({empresa.nombre_taller}) - {dias_restantes} dias restantes"
                        )
                    )

                count += 1

            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"[ERROR] Error enviando email a {empresa.nombre_taller}: {e}")
                )

        return count

    def enviar_notificacion_vencido(self, empresas, dry_run=False):
        """
        Envía notificación a empresas cuya suscripción ha vencido hoy.

        Args:
            empresas: QuerySet de empresas vencidas
            dry_run: Si True, solo simula el envío sin enviar ni marcar

        Returns:
            int: Número de notificaciones enviadas/simuladas
        """
        count = 0
        for empresa in empresas:
            try:
                # Anti-duplicado: verificar si ya se envió esta notificación
                if empresa.notificacion_vencido:
                    self.stdout.write(
                        self.style.WARNING(
                            f"[SKIP] Omitiendo {empresa.nombre_taller}: ya recibio notificacion de vencimiento"
                        )
                    )
                    continue

                # Obtener variables de soporte centralizadas
                support_email = get_support_reply_to()
                support_whatsapp_wa_me = getattr(settings, "SUPPORT_WHATSAPP_WA_ME", "56953574683")
                support_whatsapp_display = getattr(
                    settings, "SUPPORT_WHATSAPP_DISPLAY", "+56 9 5357 4683"
                )

                subject = "[URGENTE] Tu suscripcion a eGarage ha vencido"
                nombre_usuario = empresa.user.first_name or empresa.user.username
                message = f"""
{nombre_usuario},

Tu suscripción a eGarage para {empresa.nombre_taller} ha vencido hoy.

El acceso al sistema ha sido suspendido hasta que renueves tu suscripción.

Para reactivar tu cuenta:
1. Realiza tu pago por transferencia bancaria
2. Sube el comprobante en el panel de suspensión
3. Te reactivamos en 24-48 horas

No perderás tus datos - están seguros y se reactivarán cuando renueves.

Datos bancarios:
{build_transfer_payment_message(empresa.pais)}

¿Necesitas ayuda?
Email: {support_email}
WhatsApp: {support_whatsapp_display}
Link: https://wa.me/{support_whatsapp_wa_me}?text=Hola,%20mi%20suscripcion%20eGarage%20vencio,%20necesito%20ayuda

Equipo eGarage
                """

                if dry_run:
                    self.stdout.write(
                        self.style.WARNING(
                            f"[DRY-RUN] Simulando envio a {empresa.user.email} ({empresa.nombre_taller}) - SUSCRIPCION VENCIDA"
                        )
                    )
                else:
                    send_email_with_reply_to(
                        subject=subject,
                        message=message,
                        recipient_list=[empresa.user.email],
                        fail_silently=False,
                    )

                    # Marcar como notificado para evitar duplicados
                    empresa.notificacion_vencido = True
                    empresa.save(update_fields=["notificacion_vencido"])

                    self.stdout.write(
                        self.style.SUCCESS(
                            f"[OK] Email enviado a {empresa.user.email} ({empresa.nombre_taller}) - SUSCRIPCION VENCIDA"
                        )
                    )

                count += 1

            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"[ERROR] Error enviando email a {empresa.nombre_taller}: {e}")
                )

        return count
