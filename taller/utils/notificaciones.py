# taller/utils/notificaciones.py - Sistema de Envío de Notificaciones
"""
Utilidades para envío de notificaciones automáticas
"""
import logging
import smtplib
import requests
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from django.conf import settings
from django.template import Template, Context
from django.utils import timezone
from datetime import datetime, timedelta
from taller.models.notificacion import (
    TipoNotificacion, NotificacionEnviada, ConfiguracionNotificacion,
    RecordatorioMantenimiento
)
from taller.models.auditoria import LogAuditoria

logger = logging.getLogger(__name__)

class NotificacionManager:
    """Gestor principal de notificaciones"""
    
    def __init__(self, empresa):
        self.empresa = empresa
        self.config = self._get_config()
    
    def _get_config(self):
        """Obtener configuración de notificaciones para la empresa"""
        try:
            return ConfiguracionNotificacion.objects.get(empresa=self.empresa)
        except ConfiguracionNotificacion.DoesNotExist:
            # Crear configuración por defecto
            return ConfiguracionNotificacion.objects.create(empresa=self.empresa)
    
    def crear_notificacion(self, evento, destinatario_email="", destinatario_nombre="", 
                          destinatario_telefono="", documento=None, cliente=None, 
                          usuario=None, datos_extra=None):
        """Crear una notificación para envío"""
        try:
            # Buscar tipo de notificación para el evento
            tipos_notificacion = TipoNotificacion.objects.filter(
                evento=evento, 
                activo=True
            )
            
            if not tipos_notificacion.exists():
                logger.warning(f"No hay tipos de notificación configurados para {evento}")
                return []
            
            notificaciones_creadas = []
            
            for tipo_notif in tipos_notificacion:
                # Verificar si el tipo está habilitado para la empresa
                if not self._tipo_habilitado(tipo_notif.tipo):
                    continue
                
                # Renderizar mensaje
                asunto, mensaje = self._renderizar_mensaje(
                    tipo_notif, datos_extra, documento, cliente, usuario
                )
                
                # Crear notificación
                notificacion = NotificacionEnviada.objects.create(
                    empresa=self.empresa,
                    tipo_notificacion=tipo_notif,
                    destinatario_email=destinatario_email,
                    destinatario_telefono=destinatario_telefono,
                    destinatario_nombre=destinatario_nombre,
                    asunto=asunto,
                    mensaje=mensaje,
                    documento=documento,
                    cliente=cliente,
                    usuario=usuario,
                    fecha_programada=timezone.now() + timedelta(days=tipo_notif.dias_anticipacion)
                )
                
                notificaciones_creadas.append(notificacion)
                
                # Registrar en auditoría
                LogAuditoria.log_accion(
                    usuario=usuario,
                    empresa=self.empresa,
                    accion='CREATE',
                    modelo='NOTIFICACION',
                    objeto_id=notificacion.id,
                    descripcion=f"Notificación creada: {evento} -> {destinatario_nombre}"
                )
            
            return notificaciones_creadas
            
        except Exception as e:
            logger.error(f"Error creando notificación {evento}: {e}")
            return []
    
    def _tipo_habilitado(self, tipo):
        """Verificar si un tipo de notificación está habilitado"""
        if tipo == 'EMAIL':
            return self.config.email_activo
        elif tipo == 'WHATSAPP':
            return self.config.whatsapp_activo
        elif tipo == 'SMS':
            return self.config.sms_activo
        return True
    
    def _renderizar_mensaje(self, tipo_notif, datos_extra, documento=None, cliente=None, usuario=None):
        """Renderizar mensaje usando template"""
        context_data = {
            'empresa': self.empresa,
            'documento': documento,
            'cliente': cliente,
            'usuario': usuario,
            'fecha_actual': timezone.now(),
            'datos': datos_extra or {}
        }
        
        # Renderizar asunto
        asunto_template = Template(tipo_notif.template_asunto)
        asunto = asunto_template.render(Context(context_data))
        
        # Renderizar mensaje
        mensaje_template = Template(tipo_notif.template_mensaje)
        mensaje = mensaje_template.render(Context(context_data))
        
        return asunto, mensaje
    
    def procesar_notificaciones_pendientes(self):
        """Procesar cola de notificaciones pendientes"""
        ahora = timezone.now()
        
        # Verificar horario de envío
        if not self._en_horario_envio(ahora):
            return 0
        
        notificaciones = NotificacionEnviada.objects.filter(
            empresa=self.empresa,
            estado='PENDIENTE',
            fecha_programada__lte=ahora
        )
        
        enviadas = 0
        for notificacion in notificaciones:
            if self._enviar_notificacion(notificacion):
                enviadas += 1
        
        return enviadas
    
    def _en_horario_envio(self, timestamp):
        """Verificar si está en horario de envío"""
        hora_actual = timestamp.time()
        es_fin_semana = timestamp.weekday() >= 5  # Sábado = 5, Domingo = 6
        
        if es_fin_semana and not self.config.enviar_fines_semana:
            return False
        
        return self.config.hora_inicio_envio <= hora_actual <= self.config.hora_fin_envio
    
    def _enviar_notificacion(self, notificacion):
        """Enviar una notificación específica"""
        try:
            notificacion.intentos += 1
            
            if notificacion.tipo_notificacion.tipo == 'EMAIL':
                success = self._enviar_email(notificacion)
            elif notificacion.tipo_notificacion.tipo == 'WHATSAPP':
                success = self._enviar_whatsapp(notificacion)
            elif notificacion.tipo_notificacion.tipo == 'SMS':
                success = self._enviar_sms(notificacion)
            else:
                success = False
            
            if success:
                notificacion.estado = 'ENVIADO'
                notificacion.fecha_enviado = timezone.now()
                notificacion.error_mensaje = ''
            else:
                notificacion.estado = 'ERROR' if notificacion.intentos >= 3 else 'REINTENTO'
            
            notificacion.save()
            return success
            
        except Exception as e:
            logger.error(f"Error enviando notificación {notificacion.id}: {e}")
            notificacion.estado = 'ERROR'
            notificacion.error_mensaje = str(e)
            notificacion.save()
            return False
    
    def _enviar_email(self, notificacion):
        """Enviar notificación por email"""
        try:
            if not self.config.email_activo or not notificacion.destinatario_email:
                return False
            
            # Configurar SMTP
            server = smtplib.SMTP(self.config.email_smtp_host, self.config.email_smtp_port)
            server.starttls()
            server.login(self.config.email_usuario, self.config.email_password)
            
            # Crear mensaje
            msg = MIMEMultipart()
            msg['From'] = self.config.email_remitente or self.config.email_usuario
            msg['To'] = notificacion.destinatario_email
            msg['Subject'] = notificacion.asunto
            
            # Agregar logo y estilo
            mensaje_html = self._generar_email_html(notificacion.mensaje)
            msg.attach(MIMEText(mensaje_html, 'html', 'utf-8'))
            
            # Enviar
            server.send_message(msg)
            server.quit()
            
            logger.info(f"Email enviado a {notificacion.destinatario_email}")
            return True
            
        except Exception as e:
            logger.error(f"Error enviando email: {e}")
            return False
    
    def _generar_email_html(self, mensaje):
        """Generar HTML del email con estilo"""
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; }}
                .container {{ max-width: 600px; margin: 0 auto; background: white; }}
                .header {{ background: #2c3e50; color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 30px; line-height: 1.6; }}
                .footer {{ background: #ecf0f1; padding: 15px; text-align: center; font-size: 12px; color: #7f8c8d; }}
                .logo {{ max-width: 150px; margin-bottom: 10px; }}
                .button {{ background: #3498db; color: white; padding: 12px 25px; text-decoration: none; border-radius: 5px; display: inline-block; margin: 15px 0; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🚗 {self.empresa.nombre_taller}</h1>
                </div>
                <div class="content">
                    {mensaje.replace(chr(10), '<br>')}
                </div>
                <div class="footer">
                    <p>Este es un mensaje automático de {self.empresa.nombre_taller}</p>
                    <p>📧 {self.empresa.email} | 📞 {self.empresa.telefono}</p>
                    <p>📍 {self.empresa.direccion}</p>
                </div>
            </div>
        </body>
        </html>
        """
    
    def _enviar_whatsapp(self, notificacion):
        """Enviar notificación por WhatsApp (usando API)"""
        try:
            if not self.config.whatsapp_activo or not notificacion.destinatario_telefono:
                return False
            
            # URL de API de WhatsApp Business (ejemplo)
            url = "https://graph.facebook.com/v17.0/{}/messages".format(
                self.config.whatsapp_numero_business
            )
            
            headers = {
                'Authorization': f'Bearer {self.config.whatsapp_api_token}',
                'Content-Type': 'application/json'
            }
            
            data = {
                "messaging_product": "whatsapp",
                "to": notificacion.destinatario_telefono,
                "type": "text",
                "text": {
                    "body": f"🚗 *{self.empresa.nombre_taller}*\n\n{notificacion.mensaje}"
                }
            }
            
            response = requests.post(url, json=data, headers=headers, timeout=30)
            
            if response.status_code == 200:
                logger.info(f"WhatsApp enviado a {notificacion.destinatario_telefono}")
                return True
            else:
                logger.error(f"Error WhatsApp API: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Error enviando WhatsApp: {e}")
            return False
    
    def _enviar_sms(self, notificacion):
        """Enviar notificación por SMS"""
        try:
            if not self.config.sms_activo or not notificacion.destinatario_telefono:
                return False
            
            # Implementación básica para Twilio
            if self.config.sms_proveedor == 'twilio':
                from twilio.rest import Client
                
                # Configurar cliente (requiere variables de entorno)
                account_sid = getattr(settings, 'TWILIO_ACCOUNT_SID', '')
                auth_token = getattr(settings, 'TWILIO_AUTH_TOKEN', '')
                
                if not account_sid or not auth_token:
                    logger.error("Configuración de Twilio incompleta")
                    return False
                
                client = Client(account_sid, auth_token)
                
                message = client.messages.create(
                    body=f"{self.empresa.nombre_taller}: {notificacion.mensaje}",
                    from_=getattr(settings, 'TWILIO_PHONE_NUMBER', ''),
                    to=notificacion.destinatario_telefono
                )
                
                logger.info(f"SMS enviado a {notificacion.destinatario_telefono}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error enviando SMS: {e}")
            return False

# Funciones de utilidad para eventos específicos

def notificar_documento_creado(documento):
    """Notificar creación de documento"""
    manager = NotificacionManager(documento.empresa)
    
    # Notificar al cliente
    if documento.cliente and documento.cliente.email:
        datos_extra = {
            'numero_documento': documento.id,
            'fecha_documento': documento.fecha_documento,
            'total': getattr(documento, 'total', 0)
        }
        
        manager.crear_notificacion(
            evento='DOCUMENTO_CREADO',
            destinatario_email=documento.cliente.email,
            destinatario_nombre=documento.cliente.nombre,
            destinatario_telefono=getattr(documento.cliente, 'telefono', ''),
            documento=documento,
            cliente=documento.cliente,
            datos_extra=datos_extra
        )

def verificar_suscripciones_vencimiento():
    """Verificar suscripciones próximas a vencer"""
    from taller.models.empresa import Empresa
    
    empresas_por_vencer = []
    
    for empresa in Empresa.objects.filter(suscripcion_activa=True):
        dias_restantes = empresa.dias_restantes
        
        if dias_restantes <= 7 and dias_restantes > 0:  # 7 días de anticipación
            manager = NotificacionManager(empresa)
            
            if hasattr(manager.config, 'notificar_suscripcion') and manager.config.notificar_suscripcion:
                datos_extra = {
                    'dias_restantes': dias_restantes,
                    'fecha_vencimiento': empresa.fecha_expiracion
                }
                
                # Notificar al administrador de la empresa
                if empresa.usuario and empresa.usuario.email:
                    manager.crear_notificacion(
                        evento='SUSCRIPCION_VENCE',
                        destinatario_email=empresa.usuario.email,
                        destinatario_nombre=empresa.usuario.get_full_name() or empresa.usuario.username,
                        usuario=empresa.usuario,
                        datos_extra=datos_extra
                    )
                
                empresas_por_vencer.append(empresa.nombre_taller)
    
    return empresas_por_vencer

def verificar_recordatorios_mantenimiento():
    """Verificar recordatorios de mantenimiento pendientes"""
    recordatorios_enviados = 0
    
    recordatorios = RecordatorioMantenimiento.objects.filter(
        estado='PROGRAMADO',
        notificacion_enviada=False
    )
    
    for recordatorio in recordatorios:
        if recordatorio.requiere_notificacion:
            manager = NotificacionManager(recordatorio.empresa)
            
            if manager.config.notificar_mantenimiento:
                datos_extra = {
                    'tipo_mantenimiento': recordatorio.get_tipo_mantenimiento_display(),
                    'fecha_programada': recordatorio.fecha_programada,
                    'dias_restantes': recordatorio.dias_hasta_mantenimiento,
                    'vehiculo': str(recordatorio.vehiculo),
                    'descripcion': recordatorio.descripcion
                }
                
                # Notificar al cliente
                if recordatorio.cliente.email:
                    notificaciones = manager.crear_notificacion(
                        evento='MANTENIMIENTO_RECORDATORIO',
                        destinatario_email=recordatorio.cliente.email,
                        destinatario_nombre=recordatorio.cliente.nombre,
                        destinatario_telefono=getattr(recordatorio.cliente, 'telefono', ''),
                        cliente=recordatorio.cliente,
                        datos_extra=datos_extra
                    )
                    
                    if notificaciones:
                        recordatorio.notificacion_enviada = True
                        recordatorio.fecha_notificacion = timezone.now()
                        recordatorio.save()
                        recordatorios_enviados += 1
    
    return recordatorios_enviados

def procesar_cola_notificaciones():
    """Procesar todas las notificaciones pendientes de todas las empresas"""
    from taller.models.empresa import Empresa
    
    total_enviadas = 0
    
    for empresa in Empresa.objects.filter(suscripcion_activa=True):
        try:
            manager = NotificacionManager(empresa)
            enviadas = manager.procesar_notificaciones_pendientes()
            total_enviadas += enviadas
            
        except Exception as e:
            logger.error(f"Error procesando notificaciones de {empresa.nombre_taller}: {e}")
    
    return total_enviadas
