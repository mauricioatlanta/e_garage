"""
Sistema de emails para eGarage
Funciones para envío de correos electrónicos con diferenciación por país
"""

from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from django.utils.html import strip_tags
import logging

logger = logging.getLogger(__name__)

def enviar_correo_bienvenida(usuario, enlace_activacion):
    """
    Envía correo de bienvenida a nuevo usuario
    
    Args:
        usuario: Objeto User de Django
        enlace_activacion: URL completa para activar cuenta
    
    Returns:
        bool: True si se envió correctamente, False en caso contrario
    """
    try:
        # Datos del correo
        asunto = '¡Bienvenido a eGarage!'
        destinatario = [usuario.email]
        remitente = settings.DEFAULT_FROM_EMAIL
        
        # Contexto para la plantilla
        context = {
            'usuario': usuario,
            'enlace': enlace_activacion,
            'nombre_usuario': usuario.username,
            'first_name': usuario.first_name or usuario.username,
        }
        
        # Renderizar plantilla HTML
        html_content = render_to_string('emails/bienvenida.html', context)
        text_content = strip_tags(html_content)  # Versión texto plano
        
        # Crear email
        email = EmailMultiAlternatives(
            subject=asunto,
            body=text_content,
            from_email=remitente,
            to=destinatario
        )
        
        # Adjuntar versión HTML
        email.attach_alternative(html_content, "text/html")
        
        # Enviar
        email.send()
        
        logger.info(f"Correo de bienvenida enviado exitosamente a {usuario.email}")
        return True
        
    except Exception as e:
        logger.error(f"Error enviando correo de bienvenida a {usuario.email}: {str(e)}")
        return False

def enviar_correo_prueba(email_destino, nombre="Usuario"):
    """
    Envía un correo de prueba para verificar conexión SMTP
    
    Args:
        email_destino: Email donde enviar la prueba
        nombre: Nombre del destinatario
        
    Returns:
        bool: True si se envió correctamente, False en caso contrario
    """
    try:
        asunto = "Test de correo eGarage"
        remitente = settings.DEFAULT_FROM_EMAIL
        
        # Mensaje simple para prueba
        mensaje = f"""
        Hola {nombre},
        
        Este es un correo de prueba para verificar la conexión SMTP de eGarage.
        
        Si recibes este mensaje, significa que el sistema de emails está funcionando correctamente.
        
        Saludos,
        Equipo eGarage
        """
        
        # Crear email simple
        email = EmailMultiAlternatives(
            subject=asunto,
            body=mensaje,
            from_email=remitente,
            to=[email_destino]
        )
        
        # Enviar
        email.send()
        
        print(f"✅ Correo de prueba enviado exitosamente a {email_destino}")
        logger.info(f"Correo de prueba enviado exitosamente a {email_destino}")
        return True
        
    except Exception as e:
        print(f"❌ Error enviando correo de prueba a {email_destino}: {str(e)}")
        logger.error(f"Error enviando correo de prueba a {email_destino}: {str(e)}")
        return False

def enviar_correo_activacion_cuenta(usuario, codigo_activacion):
    """
    Envía correo con código de activación de cuenta
    
    Args:
        usuario: Objeto User de Django
        codigo_activacion: Código para activar la cuenta
        
    Returns:
        bool: True si se envió correctamente, False en caso contrario
    """
    try:
        asunto = "Activa tu cuenta de eGarage"
        destinatario = [usuario.email]
        remitente = settings.DEFAULT_FROM_EMAIL
        
        # Contexto para la plantilla
        context = {
            'usuario': usuario,
            'codigo': codigo_activacion,
            'nombre_usuario': usuario.first_name or usuario.username,
        }
        
        # Mensaje simple (luego se puede hacer una plantilla HTML)
        mensaje = f"""
        Hola {context['nombre_usuario']},
        
        Gracias por registrarte en eGarage.
        
        Tu código de activación es: {codigo_activacion}
        
        Para activar tu cuenta, ingresa este código en la página de activación.
        
        Saludos,
        Equipo eGarage
        """
        
        # Crear email
        email = EmailMultiAlternatives(
            subject=asunto,
            body=mensaje,
            from_email=remitente,
            to=destinatario
        )
        
        # Enviar
        email.send()
        
        logger.info(f"Correo de activación enviado exitosamente a {usuario.email}")
        return True
        
    except Exception as e:
        logger.error(f"Error enviando correo de activación a {usuario.email}: {str(e)}")
        return False

def verificar_conexion_smtp():
    """
    Verifica que la conexión SMTP esté funcionando
    
    Returns:
        dict: Resultado de la verificación con status y mensaje
    """
    try:
        from django.core.mail import get_connection
        
        connection = get_connection()
        connection.open()
        
        if connection.open():
            connection.close()
            return {
                'status': 'success',
                'mensaje': '✅ Conexión SMTP exitosa'
            }
        else:
            return {
                'status': 'error', 
                'mensaje': '❌ No se pudo establecer conexión SMTP'
            }
            
    except Exception as e:
        return {
            'status': 'error',
            'mensaje': f'❌ Error de conexión SMTP: {str(e)}'
        }
