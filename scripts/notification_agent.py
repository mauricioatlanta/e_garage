"""
Agente de notificación automática para vencimientos de trial y suscripciones
Configurado para ejecutarse como cronjob
"""

import os
import sys

import django
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils import timezone

# Configuración para usar Django desde script standalone
if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gestion_taller.settings")
    django.setup()

from taller.models import Empresa, TrialRegistro
from taller.utils.smart_logging import smart_logger


class NotificationAgent:
    """Agente inteligente de notificaciones"""

    def __init__(self):
        self.today = timezone.now().date()
        self.notifications_sent = 0
        self.errors = []

    def send_trial_expiration_warning(self, trial_registro, days_remaining):
        """Envía notificación de aviso de vencimiento de trial"""
        try:
            empresa = trial_registro.empresa
            user = trial_registro.user

            # Contexto para el template
            context = {
                "user_name": user.first_name or user.username,
                "empresa_name": empresa.nombre,
                "days_remaining": days_remaining,
                "login_url": f"{settings.SITE_URL}/accounts/login/",
                "upgrade_url": f"{settings.SITE_URL}/suscripciones/",
                "support_email": settings.DEFAULT_FROM_EMAIL,
                "today": self.today,
            }

            # Renderizar email
            subject = f"⚠️ Tu trial de eGarage expira en {days_remaining} día{'s' if days_remaining != 1 else ''}"

            # Email en HTML
            html_message = render_to_string(
                "emails/trial_expiration_warning.html", context
            )

            # Email en texto plano
            plain_message = f"""
Hola {context['user_name']},

Tu trial de eGarage para {context['empresa_name']} expira en {days_remaining} día{'s' if days_remaining != 1 else ''}.

Para continuar usando todas las funcionalidades:
1. Ingresa a tu cuenta: {context['login_url']}
2. Activa tu suscripción: {context['upgrade_url']}

¿Necesitas ayuda? Contáctanos: {context['support_email']}

Saludos,
Equipo eGarage
            """.strip()

            # Enviar email
            send_mail(
                subject=subject,
                message=plain_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                html_message=html_message,
                fail_silently=False,
            )

            # Log del envío
            smart_logger.subs_logger.info(
                f"TRIAL_WARNING_SENT | user_id: {user.id} | empresa_id: {empresa.id} | days_remaining: {days_remaining}"
            )

            self.notifications_sent += 1
            return True

        except Exception as e:
            error_msg = f"Error enviando notificación de trial a {user.email}: {str(e)}"
            self.errors.append(error_msg)
            smart_logger.subs_logger.error(error_msg)
            return False

    def send_trial_expired_notification(self, trial_registro):
        """Envía notificación de trial expirado"""
        try:
            empresa = trial_registro.empresa
            user = trial_registro.user

            context = {
                "user_name": user.first_name or user.username,
                "empresa_name": empresa.nombre,
                "login_url": f"{settings.SITE_URL}/accounts/login/",
                "upgrade_url": f"{settings.SITE_URL}/suscripciones/",
                "support_email": settings.DEFAULT_FROM_EMAIL,
                "today": self.today,
            }

            subject = "🔒 Tu trial de eGarage ha expirado - ¡Activa tu suscripción!"

            html_message = render_to_string("emails/trial_expired.html", context)

            plain_message = f"""
Hola {context['user_name']},

Tu trial de eGarage para {context['empresa_name']} ha expirado.

Para reactivar tu cuenta y continuar gestionando tu taller:
1. Activa tu suscripción: {context['upgrade_url']}
2. Ingresa a tu cuenta: {context['login_url']}

¿Tienes preguntas? Estamos aquí para ayudarte: {context['support_email']}

Saludos,
Equipo eGarage
            """.strip()

            send_mail(
                subject=subject,
                message=plain_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                html_message=html_message,
                fail_silently=False,
            )

            smart_logger.subs_logger.info(
                f"TRIAL_EXPIRED_SENT | user_id: {user.id} | empresa_id: {empresa.id}"
            )

            self.notifications_sent += 1
            return True

        except Exception as e:
            error_msg = (
                f"Error enviando notificación de expiración a {user.email}: {str(e)}"
            )
            self.errors.append(error_msg)
            smart_logger.subs_logger.error(error_msg)
            return False

    def send_subscription_expiration_warning(self, empresa, days_remaining):
        """Envía notificación de vencimiento de suscripción"""
        try:
            user = empresa.usuario

            context = {
                "user_name": user.first_name or user.username,
                "empresa_name": empresa.nombre,
                "days_remaining": days_remaining,
                "expiration_date": empresa.fecha_vencimiento_suscripcion,
                "renewal_url": f"{settings.SITE_URL}/suscripciones/renovar/",
                "support_email": settings.DEFAULT_FROM_EMAIL,
                "today": self.today,
            }

            subject = f"⏰ Tu suscripción a eGarage vence en {days_remaining} día{'s' if days_remaining != 1 else ''}"

            html_message = render_to_string(
                "emails/subscription_expiration_warning.html", context
            )

            plain_message = f"""
Hola {context['user_name']},

Tu suscripción a eGarage para {context['empresa_name']} vence en {days_remaining} día{'s' if days_remaining != 1 else ''} ({context['expiration_date']}).

Para renovar tu suscripción:
• Visita: {context['renewal_url']}
• O sube tu comprobante de pago en tu panel de control

¿Necesitas ayuda? Contáctanos: {context['support_email']}

Saludos,
Equipo eGarage
            """.strip()

            send_mail(
                subject=subject,
                message=plain_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                html_message=html_message,
                fail_silently=False,
            )

            smart_logger.subs_logger.info(
                f"SUBSCRIPTION_WARNING_SENT | empresa_id: {empresa.id} | days_remaining: {days_remaining}"
            )

            self.notifications_sent += 1
            return True

        except Exception as e:
            error_msg = (
                f"Error enviando notificación de suscripción a {user.email}: {str(e)}"
            )
            self.errors.append(error_msg)
            smart_logger.subs_logger.error(error_msg)
            return False

    def process_trial_notifications(self):
        """Procesa todas las notificaciones de trials"""
        print("🔍 Verificando trials...")

        # Trials activos
        active_trials = TrialRegistro.objects.filter(
            activo=True, fecha_expiracion__gt=self.today
        )

        for trial in active_trials:
            days_remaining = trial.dias_restantes()

            # Notificaciones en días específicos: 7, 3, 1
            if days_remaining in [7, 3, 1]:
                print(
                    f"📧 Enviando aviso de trial (quedan {days_remaining} días): {trial.user.email}"
                )
                self.send_trial_expiration_warning(trial, days_remaining)

        # Trials expirados hoy
        expired_today = TrialRegistro.objects.filter(
            activo=True, fecha_expiracion=self.today
        )

        for trial in expired_today:
            print(f"🔒 Enviando notificación de expiración: {trial.user.email}")
            self.send_trial_expired_notification(trial)

            # Marcar como expirado
            trial.expirar_si_corresponde()

    def process_subscription_notifications(self):
        """Procesa todas las notificaciones de suscripciones"""
        print("🔍 Verificando suscripciones...")

        empresas_activas = Empresa.objects.filter(
            estado_suscripcion="activa", fecha_vencimiento_suscripcion__isnull=False
        )

        for empresa in empresas_activas:
            if empresa.fecha_vencimiento_suscripcion:
                days_until_expiration = (
                    empresa.fecha_vencimiento_suscripcion - self.today
                ).days

                # Notificaciones en días específicos: 15, 7, 3, 1
                if days_until_expiration in [15, 7, 3, 1]:
                    print(
                        f"📧 Enviando aviso de suscripción (quedan {days_until_expiration} días): {empresa.usuario.email}"
                    )
                    self.send_subscription_expiration_warning(
                        empresa, days_until_expiration
                    )

    def run(self):
        """Ejecuta el agente de notificaciones"""
        print(f"🚀 Iniciando agente de notificaciones - {self.today}")

        try:
            # Procesar trials
            self.process_trial_notifications()

            # Procesar suscripciones
            self.process_subscription_notifications()

            # Resumen final
            print("\n✅ Agente completado:")
            print(f"   📧 Notificaciones enviadas: {self.notifications_sent}")
            print(f"   ❌ Errores: {len(self.errors)}")

            if self.errors:
                print("\n🚨 Errores encontrados:")
                for error in self.errors:
                    print(f"   • {error}")

            # Log del resumen
            smart_logger.subs_logger.info(
                f"NOTIFICATION_AGENT_COMPLETED | sent: {self.notifications_sent} | errors: {len(self.errors)}"
            )

        except Exception as e:
            error_msg = f"Error crítico en agente de notificaciones: {str(e)}"
            print(f"💥 {error_msg}")
            smart_logger.subs_logger.error(error_msg)
            return False

        return True


def main():
    """Función principal para ejecutar desde cronjob"""
    agent = NotificationAgent()
    success = agent.run()

    if success:
        sys.exit(0)  # Éxito
    else:
        sys.exit(1)  # Error


if __name__ == "__main__":
    main()
