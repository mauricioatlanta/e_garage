"""
Sistema de logging inteligente para eGarage
Maneja logs de autenticación, pagos, suscripciones y eventos críticos
"""

import logging
import json
from datetime import datetime, timezone
from django.conf import settings
from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone as django_timezone
from taller.models import Empresa, TrialRegistro

# Configuración de loggers especializados
def setup_smart_loggers():
    """Configura loggers especializados para diferentes eventos"""
    
    # Logger de autenticación
    auth_logger = logging.getLogger('egarage.auth')
    auth_handler = logging.FileHandler('logs/authentication.log')
    auth_formatter = logging.Formatter(
        '%(asctime)s | %(levelname)s | AUTH | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    auth_handler.setFormatter(auth_formatter)
    auth_logger.addHandler(auth_handler)
    auth_logger.setLevel(logging.INFO)
    
    # Logger de pagos
    payment_logger = logging.getLogger('egarage.payments')
    payment_handler = logging.FileHandler('logs/payments.log')
    payment_formatter = logging.Formatter(
        '%(asctime)s | %(levelname)s | PAYMENT | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    payment_handler.setFormatter(payment_formatter)
    payment_logger.addHandler(payment_handler)
    payment_logger.setLevel(logging.INFO)
    
    # Logger de suscripciones
    subs_logger = logging.getLogger('egarage.subscriptions')
    subs_handler = logging.FileHandler('logs/subscriptions.log')
    subs_formatter = logging.Formatter(
        '%(asctime)s | %(levelname)s | SUBS | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    subs_handler.setFormatter(subs_formatter)
    subs_logger.addHandler(subs_handler)
    subs_logger.setLevel(logging.INFO)
    
    return auth_logger, payment_logger, subs_logger

class SmartLogger:
    """Clase principal para logging inteligente"""
    
    def __init__(self):
        self.auth_logger = logging.getLogger('egarage.auth')
        self.payment_logger = logging.getLogger('egarage.payments')
        self.subs_logger = logging.getLogger('egarage.subscriptions')
        
    def log_login_attempt(self, username, ip_address, user_agent, success=True, reason=None):
        """Log de intentos de login"""
        log_data = {
            'username': username,
            'ip_address': ip_address,
            'user_agent': user_agent,
            'success': success,
            'timestamp': django_timezone.now().isoformat(),
            'reason': reason
        }
        
        if success:
            self.auth_logger.info(f"LOGIN_SUCCESS | {json.dumps(log_data)}")
        else:
            self.auth_logger.warning(f"LOGIN_FAILED | {json.dumps(log_data)}")
    
    def log_password_reset(self, email, ip_address, success=True):
        """Log de reset de contraseña"""
        log_data = {
            'email': email,
            'ip_address': ip_address,
            'success': success,
            'timestamp': django_timezone.now().isoformat()
        }
        
        self.auth_logger.info(f"PASSWORD_RESET | {json.dumps(log_data)}")
    
    def log_trial_activation(self, user_id, empresa_id, trial_id):
        """Log de activación de trial"""
        log_data = {
            'user_id': user_id,
            'empresa_id': empresa_id,
            'trial_id': trial_id,
            'timestamp': django_timezone.now().isoformat()
        }
        
        self.subs_logger.info(f"TRIAL_ACTIVATED | {json.dumps(log_data)}")
    
    def log_trial_expiration(self, user_id, empresa_id, trial_id, days_used):
        """Log de expiración de trial"""
        log_data = {
            'user_id': user_id,
            'empresa_id': empresa_id,
            'trial_id': trial_id,
            'days_used': days_used,
            'timestamp': django_timezone.now().isoformat()
        }
        
        self.subs_logger.info(f"TRIAL_EXPIRED | {json.dumps(log_data)}")
    
    def log_payment_received(self, empresa_id, amount, payment_method, reference=None):
        """Log de pago recibido"""
        log_data = {
            'empresa_id': empresa_id,
            'amount': str(amount),
            'payment_method': payment_method,
            'reference': reference,
            'timestamp': django_timezone.now().isoformat()
        }
        
        self.payment_logger.info(f"PAYMENT_RECEIVED | {json.dumps(log_data)}")
    
    def log_subscription_change(self, empresa_id, old_status, new_status, reason=None):
        """Log de cambio de estado de suscripción"""
        log_data = {
            'empresa_id': empresa_id,
            'old_status': old_status,
            'new_status': new_status,
            'reason': reason,
            'timestamp': django_timezone.now().isoformat()
        }
        
        self.subs_logger.info(f"SUBSCRIPTION_CHANGE | {json.dumps(log_data)}")
    
    def log_security_alert(self, event_type, details, severity="medium"):
        """Log de alertas de seguridad"""
        log_data = {
            'event_type': event_type,
            'details': details,
            'severity': severity,
            'timestamp': django_timezone.now().isoformat()
        }
        
        self.auth_logger.warning(f"SECURITY_ALERT | {json.dumps(log_data)}")
    
    def log_middleware_block(self, user_id, empresa_id, middleware_name, reason):
        """Log de bloqueos por middleware"""
        log_data = {
            'user_id': user_id,
            'empresa_id': empresa_id,
            'middleware': middleware_name,
            'reason': reason,
            'timestamp': django_timezone.now().isoformat()
        }
        
        self.auth_logger.info(f"MIDDLEWARE_BLOCK | {json.dumps(log_data)}")

# Instancia global
smart_logger = SmartLogger()

# Función de utilidad para obtener IP del request
def get_client_ip(request):
    """Obtiene la IP real del cliente"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

# Función de utilidad para obtener User Agent
def get_user_agent(request):
    """Obtiene el User Agent del request"""
    return request.META.get('HTTP_USER_AGENT', 'Unknown')

# Decorador para logging automático de vistas
def log_auth_view(view_func):
    """Decorador para logging automático de vistas de autenticación"""
    def wrapper(request, *args, **kwargs):
        ip = get_client_ip(request)
        user_agent = get_user_agent(request)
        
        try:
            response = view_func(request, *args, **kwargs)
            
            # Log exitoso si no hay excepción
            if hasattr(request, 'user') and request.user.is_authenticated:
                smart_logger.log_login_attempt(
                    username=request.user.username,
                    ip_address=ip,
                    user_agent=user_agent,
                    success=True
                )
            
            return response
            
        except Exception as e:
            # Log del error
            smart_logger.log_security_alert(
                event_type="view_exception",
                details={
                    'view': view_func.__name__,
                    'error': str(e),
                    'ip': ip,
                    'user_agent': user_agent
                },
                severity="high"
            )
            raise
    
    return wrapper

# Función para crear directorios de logs
def ensure_log_directories():
    """Asegura que existan los directorios de logs"""
    import os
    log_dir = os.path.join(settings.BASE_DIR, 'logs')
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

# Inicialización automática
ensure_log_directories()
setup_smart_loggers()
