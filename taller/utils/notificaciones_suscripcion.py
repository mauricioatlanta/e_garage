# taller/utils/notificaciones_suscripcion.py
"""
Módulo de notificaciones para eventos de suscripción
Incluye: Nueva Suscripción, Cambio de Plan, Renovación Exitosa
Envía notificaciones por Email y WhatsApp automáticamente
"""

import logging
from datetime import timedelta

import requests
from django.conf import settings
from django.template.loader import render_to_string
from django.utils import timezone
from taller.utils.email_helper import get_branded_from_email, send_email_with_reply_to

logger = logging.getLogger(__name__)


def obtener_url_login(empresa):
    """Obtener URL de login según el país de la empresa"""
    base_url = getattr(settings, "SITE_URL", "https://egarage.cl")

    if empresa.pais == "CL":
        return f"{base_url}/cl/es/accounts/login/"
    elif empresa.pais == "MX":
        return f"{base_url}/mx/es/accounts/login/"
    elif empresa.pais == "US":
        return f"{base_url}/us/en/accounts/login/"
    else:
        return f"{base_url}/accounts/login/"


def obtener_idioma(empresa):
    """Obtener idioma según el país"""
    if empresa.pais == "US":
        return "en"
    return "es"


def obtener_moneda(empresa):
    """Obtener moneda según el país"""
    if empresa.pais == "CL":
        return "CLP"
    elif empresa.pais == "MX":
        return "MXN"
    else:
        return "USD"


def enviar_whatsapp(empresa, mensaje):
    """
    Enviar mensaje por WhatsApp usando la API configurada
    """
    try:
        from taller.models.notificacion import ConfiguracionNotificacion

        # Obtener configuración de notificaciones
        try:
            config = ConfiguracionNotificacion.objects.get(empresa=empresa)
        except ConfiguracionNotificacion.DoesNotExist:
            logger.warning(f"No hay configuración de WhatsApp para {empresa.nombre_taller}")
            return False

        if not config.whatsapp_activo or not empresa.telefono:
            return False

        # URL de API de WhatsApp Business
        url = f"https://graph.facebook.com/v17.0/{config.whatsapp_numero_business}/messages"

        headers = {
            "Authorization": f"Bearer {config.whatsapp_api_token}",
            "Content-Type": "application/json",
        }

        data = {
            "messaging_product": "whatsapp",
            "to": empresa.telefono.replace("+", "").replace(" ", "").replace("-", ""),
            "type": "text",
            "text": {"body": mensaje},
        }

        response = requests.post(url, json=data, headers=headers, timeout=30)

        if response.status_code == 200:
            logger.info(f"WhatsApp enviado a {empresa.telefono}")
            return True
        else:
            logger.error(f"Error WhatsApp API: {response.status_code} - {response.text}")
            return False

    except Exception as e:
        logger.error(f"Error enviando WhatsApp: {e}")
        return False


def enviar_whatsapp_a_numero(numero_telefono, mensaje, empresa=None):
    """
    Enviar mensaje por WhatsApp a un número específico sin necesidad de objeto empresa

    Args:
        numero_telefono: Número de teléfono destino (ej: "+56963607348")
        mensaje: Mensaje a enviar
        empresa: (Opcional) Empresa para obtener configuración. Si no se proporciona,
                 intentará obtener la primera configuración activa disponible.

    Returns:
        bool: True si se envió correctamente, False en caso contrario
    """
    try:
        from taller.models.notificacion import ConfiguracionNotificacion

        # Obtener configuración de WhatsApp
        config = None

        if empresa:
            # Intentar obtener configuración de la empresa proporcionada
            try:
                config = ConfiguracionNotificacion.objects.get(empresa=empresa)
            except ConfiguracionNotificacion.DoesNotExist:
                pass

        # Si no hay configuración de empresa, buscar la primera configuración activa
        if not config:
            try:
                config = ConfiguracionNotificacion.objects.filter(
                    whatsapp_activo=True,
                    whatsapp_api_token__isnull=False,
                    whatsapp_api_token__gt="",
                    whatsapp_numero_business__isnull=False,
                    whatsapp_numero_business__gt="",
                ).first()
            except Exception:
                pass

        # Si aún no hay configuración, intentar desde settings
        if not config:
            whatsapp_token = getattr(settings, "WHATSAPP_API_TOKEN", None)
            whatsapp_business_id = getattr(settings, "WHATSAPP_BUSINESS_ID", None)

            if whatsapp_token and whatsapp_business_id:
                # Crear objeto temporal con configuración de settings
                class TempConfig:
                    whatsapp_api_token = whatsapp_token
                    whatsapp_numero_business = whatsapp_business_id

                config = TempConfig()

        if not config:
            logger.warning("No se encontró configuración de WhatsApp disponible")
            return False

        if not hasattr(config, "whatsapp_api_token") or not config.whatsapp_api_token:
            logger.warning("Token de WhatsApp no configurado")
            return False

        if not hasattr(config, "whatsapp_numero_business") or not config.whatsapp_numero_business:
            logger.warning("Número de WhatsApp Business no configurado")
            return False

        # Limpiar número de teléfono (remover +, espacios, guiones)
        numero_limpio = numero_telefono.replace("+", "").replace(" ", "").replace("-", "")

        # URL de API de WhatsApp Business
        url = f"https://graph.facebook.com/v17.0/{config.whatsapp_numero_business}/messages"

        headers = {
            "Authorization": f"Bearer {config.whatsapp_api_token}",
            "Content-Type": "application/json",
        }

        data = {
            "messaging_product": "whatsapp",
            "to": numero_limpio,
            "type": "text",
            "text": {"body": mensaje},
        }

        response = requests.post(url, json=data, headers=headers, timeout=30)

        if response.status_code == 200:
            logger.info(f"WhatsApp de auditoría enviado a {numero_telefono}")
            return True
        else:
            logger.error(f"Error WhatsApp API: {response.status_code} - {response.text}")
            return False

    except Exception as e:
        logger.error(f"Error enviando WhatsApp de auditoría: {e}", exc_info=True)
        return False


def notificar_nueva_suscripcion(empresa, plan, monto, es_nueva_empresa=False, send_email=True):
    """
    A. NUEVA SUSCRIPCIÓN
    Envía Email de Bienvenida + WhatsApp
    Debe incluir: Credenciales (usuario/correo), enlace de ingreso y resumen del plan
    """
    try:
        language = obtener_idioma(empresa)
        moneda = obtener_moneda(empresa)
        url_login = obtener_url_login(empresa)

        # Obtener nombre del plan
        plan_display = dict(empresa.PLAN_CHOICES).get(plan, plan)

        # Preparar contexto para el email
        context = {
            "empresa": empresa,
            "usuario": empresa.user,
            "plan": plan,
            "plan_display": plan_display,
            "monto": monto,
            "moneda": moneda,
            "fecha_inicio": empresa.fecha_inicio,
            "fecha_fin": empresa.fecha_fin,
            "url_login": url_login,
            "email_usuario": empresa.user.email,
            "username": empresa.user.username,
            "language": language,
            "es_nueva_empresa": es_nueva_empresa,
        }
        email_sender = send_email_with_reply_to if send_email else (lambda *args, **kwargs: 0)

        # === ENVIAR EMAIL ===
        try:
            if language == "en":
                subject = "🎉 Welcome to eGarage - Your Subscription is Active!"
            else:
                subject = "🎉 ¡Bienvenido a eGarage - Tu Suscripción está Activa!"

            html_message = render_to_string("emails/suscripcion_confirmada.html", context)

            # Versión texto plano
            if language == "en":
                plain_message = f"""
Welcome to eGarage!

Your subscription has been successfully activated.

ACCOUNT DETAILS:
- Username: {empresa.user.username}
- Email: {empresa.user.email}
- Login URL: {url_login}

SUBSCRIPTION DETAILS:
- Plan: {plan_display}
- Amount: ${monto} {moneda}
- Start Date: {empresa.fecha_inicio.strftime('%Y-%m-%d')}
- Expiration Date: {empresa.fecha_fin.strftime('%Y-%m-%d') if empresa.fecha_fin else 'N/A'}

Thank you for choosing eGarage!

Best regards,
The eGarage Team
                """.strip()
            else:
                plain_message = f"""
¡Bienvenido a eGarage!

Tu suscripción ha sido activada exitosamente.

DETALLES DE CUENTA:
- Usuario: {empresa.user.username}
- Correo: {empresa.user.email}
- Enlace de ingreso: {url_login}

DETALLES DE SUSCRIPCIÓN:
- Plan: {plan_display}
- Monto: ${monto} {moneda}
- Fecha de inicio: {empresa.fecha_inicio.strftime('%d/%m/%Y')}
- Fecha de expiración: {empresa.fecha_fin.strftime('%d/%m/%Y') if empresa.fecha_fin else 'N/A'}

¡Gracias por elegir eGarage!

Saludos,
Equipo eGarage
                """.strip()

            email_sender(
                subject=subject,
                message=plain_message,
                from_email=get_branded_from_email(settings.DEFAULT_FROM_EMAIL),
                recipient_list=(
                    [empresa.user.email, empresa.email]
                    if empresa.email != empresa.user.email
                    else [empresa.user.email]
                ),
                html_message=html_message,
                fail_silently=False,
            )

            logger.info(f"✅ Email de nueva suscripción enviado a {empresa.user.email}")

        except Exception as e:
            logger.error(f"⚠️ Error al enviar email de nueva suscripción: {str(e)}")

        # === ENVIAR WHATSAPP ===
        try:
            if language == "en":
                whatsapp_message = f"""🚗 *Welcome to eGarage!*

Your subscription is now active.

*Account Details:*
👤 Username: {empresa.user.username}
📧 Email: {empresa.user.email}
🔗 Login: {url_login}

*Subscription:*
📦 Plan: {plan_display}
💰 Amount: ${monto} {moneda}
📅 Valid until: {empresa.fecha_fin.strftime('%Y-%m-%d') if empresa.fecha_fin else 'N/A'}

Thank you for choosing eGarage! 🎉"""
            else:
                whatsapp_message = f"""🚗 *¡Bienvenido a eGarage!*

Tu suscripción ya está activa.

*Detalles de Cuenta:*
👤 Usuario: {empresa.user.username}
📧 Correo: {empresa.user.email}
🔗 Ingreso: {url_login}

*Suscripción:*
📦 Plan: {plan_display}
💰 Monto: ${monto} {moneda}
📅 Válido hasta: {empresa.fecha_fin.strftime('%d/%m/%Y') if empresa.fecha_fin else 'N/A'}

¡Gracias por elegir eGarage! 🎉"""

            enviar_whatsapp(empresa, whatsapp_message)
            logger.info(f"✅ WhatsApp de nueva suscripción enviado a {empresa.telefono}")

        except Exception as e:
            logger.error(f"⚠️ Error al enviar WhatsApp de nueva suscripción: {str(e)}")

        # === NOTIFICAR AL ADMIN DE EGARAGE ===
        # 🔒 IDEMPOTENCIA: Usar flag en memoria + comprobante_pago_id/pago_pendiente_id si está disponible
        if not getattr(empresa, "_admin_whatsapp_notified", False):
            try:
                from taller.whatsapp.admin_notifications import notify_admin_new_subscription

                # Intentar obtener IDs de pago/comprobante desde el contexto si están disponibles
                comprobante_pago_id = getattr(empresa, "_current_comprobante_pago_id", None)
                pago_pendiente_id = getattr(empresa, "_current_pago_pendiente_id", None)

                notify_admin_new_subscription(
                    empresa=empresa,
                    plan=plan,
                    monto=monto,
                    es_nueva_suscripcion=True,
                    comprobante_pago_id=comprobante_pago_id,
                    pago_pendiente_id=pago_pendiente_id,
                )
                # Marcar como notificado para evitar duplicados en esta operación
                empresa._admin_whatsapp_notified = True
            except Exception as e:
                # 🔒 FAIL-SAFE: No romper flujo si falla notificación admin
                logger.error(
                    f"⚠️ Error al notificar admin de nueva suscripción (ignorado): {str(e)}"
                )

        return True

    except Exception as e:
        logger.error(f"Error en notificar_nueva_suscripcion: {e}")
        return False


def notificar_cambio_plan(empresa, plan_anterior, plan_nuevo, monto, fecha_inicio, send_email=True):
    """
    B. CAMBIO DE PLAN
    Envía Email de Confirmación + WhatsApp
    Debe incluir: Agradecimiento, detalles del nuevo plan (nombre, fecha de inicio) y fecha de expiración
    """
    try:
        language = obtener_idioma(empresa)
        moneda = obtener_moneda(empresa)

        # Obtener nombres de los planes
        plan_anterior_display = dict(empresa.PLAN_CHOICES).get(plan_anterior, plan_anterior)
        plan_nuevo_display = dict(empresa.PLAN_CHOICES).get(plan_nuevo, plan_nuevo)

        # Preparar contexto
        context = {
            "empresa": empresa,
            "usuario": empresa.user,
            "plan_anterior": plan_anterior,
            "plan_anterior_display": plan_anterior_display,
            "plan_nuevo": plan_nuevo,
            "plan_nuevo_display": plan_nuevo_display,
            "monto": monto,
            "moneda": moneda,
            "fecha_inicio": fecha_inicio,
            "fecha_fin": empresa.fecha_fin,
            "language": language,
        }
        email_sender = send_email_with_reply_to if send_email else (lambda *args, **kwargs: 0)

        # === ENVIAR EMAIL ===
        try:
            if language == "en":
                subject = "✅ Plan Changed Successfully - eGarage"
            else:
                subject = "✅ Plan Cambiado Exitosamente - eGarage"

            html_message = render_to_string("email/cambio_plan.html", context)

            # Versión texto plano
            if language == "en":
                plain_message = f"""
Thank you for your trust in eGarage!

Your subscription plan has been successfully changed.

PLAN CHANGE DETAILS:
- Previous Plan: {plan_anterior_display}
- New Plan: {plan_nuevo_display}
- Amount: ${monto} {moneda}
- Start Date: {fecha_inicio.strftime('%Y-%m-%d')}
- Expiration Date: {empresa.fecha_fin.strftime('%Y-%m-%d') if empresa.fecha_fin else 'N/A'}

You can now enjoy all the benefits of your new plan.

Best regards,
The eGarage Team
                """.strip()
            else:
                plain_message = f"""
¡Gracias por tu confianza en eGarage!

Tu plan de suscripción ha sido cambiado exitosamente.

DETALLES DEL CAMBIO:
- Plan Anterior: {plan_anterior_display}
- Plan Nuevo: {plan_nuevo_display}
- Monto: ${monto} {moneda}
- Fecha de Inicio: {fecha_inicio.strftime('%d/%m/%Y')}
- Fecha de Expiración: {empresa.fecha_fin.strftime('%d/%m/%Y') if empresa.fecha_fin else 'N/A'}

Ya puedes disfrutar de todos los beneficios de tu nuevo plan.

Saludos,
Equipo eGarage
                """.strip()

            email_sender(
                subject=subject,
                message=plain_message,
                from_email=get_branded_from_email(settings.DEFAULT_FROM_EMAIL),
                recipient_list=(
                    [empresa.user.email, empresa.email]
                    if empresa.email != empresa.user.email
                    else [empresa.user.email]
                ),
                html_message=html_message,
                fail_silently=False,
            )

            logger.info(f"✅ Email de cambio de plan enviado a {empresa.user.email}")

        except Exception as e:
            logger.error(f"⚠️ Error al enviar email de cambio de plan: {str(e)}")

        # === ENVIAR WHATSAPP ===
        try:
            if language == "en":
                whatsapp_message = f"""✅ *Plan Changed Successfully*

Thank you for your trust in eGarage!

*Change Details:*
📦 Previous: {plan_anterior_display}
📦 New: {plan_nuevo_display}
💰 Amount: ${monto} {moneda}
📅 Start: {fecha_inicio.strftime('%Y-%m-%d')}
📅 Expires: {empresa.fecha_fin.strftime('%Y-%m-%d') if empresa.fecha_fin else 'N/A'}

Enjoy your new plan! 🎉"""
            else:
                whatsapp_message = f"""✅ *Plan Cambiado Exitosamente*

¡Gracias por tu confianza en eGarage!

*Detalles del Cambio:*
📦 Anterior: {plan_anterior_display}
📦 Nuevo: {plan_nuevo_display}
💰 Monto: ${monto} {moneda}
📅 Inicio: {fecha_inicio.strftime('%d/%m/%Y')}
📅 Expira: {empresa.fecha_fin.strftime('%d/%m/%Y') if empresa.fecha_fin else 'N/A'}

¡Disfruta tu nuevo plan! 🎉"""

            enviar_whatsapp(empresa, whatsapp_message)
            logger.info(f"✅ WhatsApp de cambio de plan enviado a {empresa.telefono}")

        except Exception as e:
            logger.error(f"⚠️ Error al enviar WhatsApp de cambio de plan: {str(e)}")

        return True

    except Exception as e:
        logger.error(f"Error en notificar_cambio_plan: {e}")
        return False


def notificar_renovacion_exitosa(
    empresa,
    plan,
    monto,
    dias_renovados,
    is_courtesy=False,
    duration_months=None,
    send_email=True,
):
    """
    C. RENOVACIÓN EXITOSA
    Envía Email de Confirmación + WhatsApp
    Debe incluir: Agradecimiento por la confianza en eGarage y detalles del nuevo periodo

    Args:
        empresa: Instancia de Empresa
        plan: Plan de suscripción
        monto: Monto de la renovación (0 para cortesías)
        dias_renovados: Días renovados
        is_courtesy: Si True, es una cortesía administrativa
        duration_months: Meses otorgados (para cortesías: 1, 6 o 12)
    """
    try:
        language = obtener_idioma(empresa)
        moneda = obtener_moneda(empresa)

        # Obtener nombre del plan
        plan_display = dict(empresa.PLAN_CHOICES).get(plan, plan)

        # Preparar mensaje de cortesía si aplica
        if is_courtesy and duration_months:
            if duration_months == 1:
                periodo_cortesia = "1 mes" if language == "es" else "1 month"
            elif duration_months == 6:
                periodo_cortesia = "6 meses" if language == "es" else "6 months"
            else:  # 12
                periodo_cortesia = "1 año" if language == "es" else "1 year"
        else:
            periodo_cortesia = None

        # Preparar contexto
        context = {
            "empresa": empresa,
            "usuario": empresa.user,
            "plan": plan,
            "plan_display": plan_display,
            "monto": monto,
            "moneda": moneda,
            "fecha_inicio": empresa.fecha_inicio,
            "fecha_fin": empresa.fecha_fin,
            "dias_renovados": dias_renovados,
            "language": language,
            "is_courtesy": is_courtesy,
            "periodo_cortesia": periodo_cortesia,
            "duration_months": duration_months,
        }
        email_sender = send_email_with_reply_to if send_email else (lambda *args, **kwargs: 0)

        # === ENVIAR EMAIL ===
        try:
            if is_courtesy:
                if language == "en":
                    subject = "🎁 Courtesy Extension Granted - eGarage"
                else:
                    subject = "🎁 Extensión de Cortesía Otorgada - eGarage"
            else:
                if language == "en":
                    subject = "✅ Subscription Renewed Successfully - eGarage"
                else:
                    subject = "✅ Suscripción Renovada Exitosamente - eGarage"

            html_message = render_to_string("email/renovacion_exitosa.html", context)

            # Versión texto plano
            if is_courtesy:
                # Mensaje especial para cortesía
                if language == "en":
                    plain_message = f"""
Thank you for your support! Your subscription has been extended by {periodo_cortesia} as a courtesy for helping us become the world's #1 platform.

COURTESY EXTENSION DETAILS:
- Plan: {plan_display}
- Period Extended: {periodo_cortesia} (FREE)
- New Expiration Date: {empresa.fecha_fin.strftime('%Y-%m-%d') if empresa.fecha_fin else 'N/A'}

We appreciate your loyalty and look forward to continuing to serve you.

Best regards,
The eGarage Team
                    """.strip()
                else:
                    plain_message = f"""
¡Gracias por tu apoyo! Tu suscripción ha sido extendida por {periodo_cortesia} como cortesía por ayudarnos a ser la plataforma número 1 del mundo.

DETALLES DE EXTENSIÓN DE CORTESÍA:
- Plan: {plan_display}
- Período Extendido: {periodo_cortesia} (GRATIS)
- Nueva Fecha de Expiración: {empresa.fecha_fin.strftime('%d/%m/%Y') if empresa.fecha_fin else 'N/A'}

Apreciamos tu lealtad y esperamos seguir sirviéndote.

Saludos,
Equipo eGarage
                    """.strip()
            else:
                # Mensaje estándar de renovación
                if language == "en":
                    plain_message = f"""
Thank you for your continued trust in eGarage!

Your subscription has been successfully renewed.

RENEWAL DETAILS:
- Plan: {plan_display}
- Amount: ${monto} {moneda}
- Period: {dias_renovados} days
- New Expiration Date: {empresa.fecha_fin.strftime('%Y-%m-%d') if empresa.fecha_fin else 'N/A'}

We appreciate your loyalty and look forward to continuing to serve you.

Best regards,
The eGarage Team
                    """.strip()
                else:
                    plain_message = f"""
¡Gracias por tu continua confianza en eGarage!

Tu suscripción ha sido renovada exitosamente.

DETALLES DE RENOVACIÓN:
- Plan: {plan_display}
- Monto: ${monto} {moneda}
- Período: {dias_renovados} días
- Nueva Fecha de Expiración: {empresa.fecha_fin.strftime('%d/%m/%Y') if empresa.fecha_fin else 'N/A'}

Apreciamos tu lealtad y esperamos seguir sirviéndote.

Saludos,
Equipo eGarage
                    """.strip()

            email_sender(
                subject=subject,
                message=plain_message,
                from_email=get_branded_from_email(settings.DEFAULT_FROM_EMAIL),
                recipient_list=(
                    [empresa.user.email, empresa.email]
                    if empresa.email != empresa.user.email
                    else [empresa.user.email]
                ),
                html_message=html_message,
                fail_silently=False,
            )

            logger.info(f"✅ Email de renovación exitosa enviado a {empresa.user.email}")

        except Exception as e:
            logger.error(f"⚠️ Error al enviar email de renovación: {str(e)}")

            # === ENVIAR WHATSAPP ===
        try:
            if is_courtesy:
                # Mensaje especial para cortesía
                if language == "en":
                    whatsapp_message = f"""🎁 *Courtesy Extension Granted*

Thank you for your support! Your subscription has been extended by {periodo_cortesia} as a courtesy for helping us become the world's #1 platform.

*Extension Details:*
📦 Plan: {plan_display}
🎁 Period: {periodo_cortesia} (FREE)
📅 Expires: {empresa.fecha_fin.strftime('%Y-%m-%d') if empresa.fecha_fin else 'N/A'}

We appreciate your loyalty! 🙏"""
                else:
                    whatsapp_message = f"""🎁 *Extensión de Cortesía Otorgada*

¡Gracias por tu apoyo! Tu suscripción ha sido extendida por {periodo_cortesia} como cortesía por ayudarnos a ser la plataforma número 1 del mundo.

*Detalles de Extensión:*
📦 Plan: {plan_display}
🎁 Período: {periodo_cortesia} (GRATIS)
📅 Expira: {empresa.fecha_fin.strftime('%d/%m/%Y') if empresa.fecha_fin else 'N/A'}

¡Apreciamos tu lealtad! 🙏"""
            else:
                # Mensaje estándar de renovación
                if language == "en":
                    whatsapp_message = f"""✅ *Subscription Renewed Successfully*

Thank you for your continued trust in eGarage!

*Renewal Details:*
📦 Plan: {plan_display}
💰 Amount: ${monto} {moneda}
📅 Period: {dias_renovados} days
📅 Expires: {empresa.fecha_fin.strftime('%Y-%m-%d') if empresa.fecha_fin else 'N/A'}

We appreciate your loyalty! 🙏"""
                else:
                    whatsapp_message = f"""✅ *Suscripción Renovada Exitosamente*

¡Gracias por tu continua confianza en eGarage!

*Detalles de Renovación:*
📦 Plan: {plan_display}
💰 Monto: ${monto} {moneda}
📅 Período: {dias_renovados} días
📅 Expira: {empresa.fecha_fin.strftime('%d/%m/%Y') if empresa.fecha_fin else 'N/A'}

¡Apreciamos tu lealtad! 🙏"""

            enviar_whatsapp(empresa, whatsapp_message)
            logger.info(f"✅ WhatsApp de renovación exitosa enviado a {empresa.telefono}")

        except Exception as e:
            logger.error(f"⚠️ Error al enviar WhatsApp de renovación: {str(e)}")

        # === NOTIFICAR AL ADMIN DE EGARAGE ===
        # 🔒 IDEMPOTENCIA: Usar flag en memoria + comprobante_pago_id/pago_pendiente_id si está disponible
        if not getattr(empresa, "_admin_whatsapp_notified", False):
            try:
                from taller.whatsapp.admin_notifications import notify_admin_new_subscription

                # Intentar obtener IDs de pago/comprobante desde el contexto si están disponibles
                comprobante_pago_id = getattr(empresa, "_current_comprobante_pago_id", None)
                pago_pendiente_id = getattr(empresa, "_current_pago_pendiente_id", None)

                notify_admin_new_subscription(
                    empresa=empresa,
                    plan=plan,
                    monto=monto,
                    es_nueva_suscripcion=False,
                    dias_renovados=dias_renovados,
                    comprobante_pago_id=comprobante_pago_id,
                    pago_pendiente_id=pago_pendiente_id,
                )
                # Marcar como notificado para evitar duplicados en esta operación
                empresa._admin_whatsapp_notified = True
            except Exception as e:
                # 🔒 FAIL-SAFE: No romper flujo si falla notificación admin
                logger.error(f"⚠️ Error al notificar admin de renovación (ignorado): {str(e)}")

        return True

    except Exception as e:
        logger.error(f"Error en notificar_renovacion_exitosa: {e}")
        return False
