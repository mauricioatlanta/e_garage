"""
Sistema de Rate Limiting para login y vistas sensibles
Previene ataques de fuerza bruta y protege contra spam
"""

from django.core.cache import cache
from django.http import HttpResponse
from django.shortcuts import render
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache
from functools import wraps
import time
from datetime import datetime, timedelta
from taller.utils.smart_logging import smart_logger, get_client_ip, get_user_agent


class RateLimiter:
    """Sistema de rate limiting inteligente"""
    
    def __init__(self):
        self.cache_prefix = "rate_limit"
        
        # Configuraciones por tipo de acción
        self.limits = {
            'login': {
                'attempts': 5,      # Intentos permitidos
                'window': 900,      # Ventana de tiempo (15 minutos)
                'block_time': 1800  # Tiempo de bloqueo (30 minutos)
            },
            'password_reset': {
                'attempts': 3,
                'window': 3600,     # 1 hora
                'block_time': 3600  # 1 hora de bloqueo
            },
            'registration': {
                'attempts': 3,
                'window': 3600,
                'block_time': 1800
            },
            'api_call': {
                'attempts': 100,
                'window': 60,       # 1 minuto
                'block_time': 300   # 5 minutos
            }
        }
    
    def get_cache_key(self, action, identifier):
        """Genera clave única para el cache"""
        return f"{self.cache_prefix}:{action}:{identifier}"
    
    def get_block_key(self, action, identifier):
        """Genera clave para bloqueos"""
        return f"{self.cache_prefix}:block:{action}:{identifier}"
    
    def is_blocked(self, action, identifier):
        """Verifica si una IP/usuario está bloqueado"""
        block_key = self.get_block_key(action, identifier)
        blocked_until = cache.get(block_key)
        
        if blocked_until:
            if time.time() < blocked_until:
                return True
            else:
                # El bloqueo expiró, limpiar
                cache.delete(block_key)
                return False
        
        return False
    
    def block_identifier(self, action, identifier):
        """Bloquea una IP/usuario por el tiempo configurado"""
        config = self.limits.get(action, self.limits['login'])
        block_key = self.get_block_key(action, identifier)
        block_until = time.time() + config['block_time']
        
        cache.set(block_key, block_until, config['block_time'])
        
        # Log del bloqueo
        smart_logger.log_security_alert(
            event_type="rate_limit_block",
            details={
                'action': action,
                'identifier': identifier,
                'block_until': datetime.fromtimestamp(block_until).isoformat(),
                'block_duration': config['block_time']
            },
            severity="high"
        )
    
    def check_rate_limit(self, action, identifier):
        """
        Verifica rate limit para una acción e identificador
        Retorna: (allowed: bool, attempts_left: int, reset_time: timestamp)
        """
        # Verificar si está bloqueado
        if self.is_blocked(action, identifier):
            block_key = self.get_block_key(action, identifier)
            blocked_until = cache.get(block_key)
            return False, 0, blocked_until
        
        config = self.limits.get(action, self.limits['login'])
        cache_key = self.get_cache_key(action, identifier)
        
        # Obtener intentos actuales
        attempts_data = cache.get(cache_key, {'count': 0, 'reset_time': time.time() + config['window']})
        
        current_time = time.time()
        
        # Si la ventana expiró, reiniciar contador
        if current_time > attempts_data['reset_time']:
            attempts_data = {'count': 0, 'reset_time': current_time + config['window']}
        
        # Verificar límite
        if attempts_data['count'] >= config['attempts']:
            # Límite excedido, bloquear
            self.block_identifier(action, identifier)
            return False, 0, time.time() + config['block_time']
        
        # Incrementar contador
        attempts_data['count'] += 1
        cache.set(cache_key, attempts_data, config['window'])
        
        attempts_left = config['attempts'] - attempts_data['count']
        return True, attempts_left, attempts_data['reset_time']
    
    def reset_attempts(self, action, identifier):
        """Reinicia el contador de intentos (usado en login exitoso)"""
        cache_key = self.get_cache_key(action, identifier)
        cache.delete(cache_key)
    
    def get_remaining_block_time(self, action, identifier):
        """Obtiene tiempo restante de bloqueo en segundos"""
        if not self.is_blocked(action, identifier):
            return 0
        
        block_key = self.get_block_key(action, identifier)
        blocked_until = cache.get(block_key, 0)
        remaining = max(0, blocked_until - time.time())
        return int(remaining)


# Instancia global
rate_limiter = RateLimiter()


def rate_limit(action='login', per_ip=True, per_user=False):
    """
    Decorador para aplicar rate limiting a vistas
    
    Args:
        action: tipo de acción para el rate limit
        per_ip: aplicar límite por IP
        per_user: aplicar límite por usuario (requiere usuario autenticado)
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            identifiers = []
            
            # Rate limit por IP
            if per_ip:
                ip = get_client_ip(request)
                identifiers.append(f"ip:{ip}")
            
            # Rate limit por usuario
            if per_user and request.user.is_authenticated:
                identifiers.append(f"user:{request.user.id}")
            
            # Verificar rate limits
            for identifier in identifiers:
                allowed, attempts_left, reset_time = rate_limiter.check_rate_limit(action, identifier)
                
                if not allowed:
                    # Rate limit excedido
                    remaining_time = rate_limiter.get_remaining_block_time(action, identifier)
                    
                    # Log del bloqueo
                    smart_logger.log_security_alert(
                        event_type="rate_limit_exceeded",
                        details={
                            'action': action,
                            'identifier': identifier,
                            'ip': get_client_ip(request),
                            'user_agent': get_user_agent(request),
                            'view': view_func.__name__,
                            'remaining_block_time': remaining_time
                        },
                        severity="medium"
                    )
                    
                    # Respuesta de rate limit
                    if request.headers.get('Content-Type') == 'application/json':
                        # Respuesta JSON para API
                        from django.http import JsonResponse
                        return JsonResponse({
                            'error': 'rate_limit_exceeded',
                            'message': f'Demasiados intentos. Intenta de nuevo en {remaining_time // 60} minutos.',
                            'retry_after': remaining_time
                        }, status=429)
                    else:
                        # Respuesta HTML para web
                        context = {
                            'action': action,
                            'remaining_time': remaining_time,
                            'remaining_minutes': remaining_time // 60,
                            'remaining_seconds': remaining_time % 60
                        }
                        return render(request, 'errors/rate_limit.html', context, status=429)
            
            # Continuar con la vista
            response = view_func(request, *args, **kwargs)
            
            # Si el login fue exitoso, reiniciar contadores
            if (action == 'login' and 
                hasattr(response, 'status_code') and 
                response.status_code in [200, 302] and
                request.method == 'POST'):
                
                for identifier in identifiers:
                    rate_limiter.reset_attempts(action, identifier)
            
            return response
        
        return wrapper
    return decorator


def smart_rate_limit(action='login'):
    """
    Rate limiting inteligente que se adapta según el comportamiento
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            ip = get_client_ip(request)
            user_agent = get_user_agent(request)
            
            # Identificador compuesto
            identifier = f"ip:{ip}"
            
            # Rate limiting más estricto para comportamiento sospechoso
            suspicious_indicators = [
                len(user_agent) < 20,  # User agent muy corto
                'bot' in user_agent.lower(),  # Bots
                'curl' in user_agent.lower(),  # Herramientas de línea de comandos
                'wget' in user_agent.lower(),
                'python' in user_agent.lower(),
            ]
            
            if any(suspicious_indicators):
                # Rate limit más estricto para comportamiento sospechoso
                custom_config = {
                    'attempts': 2,
                    'window': 600,
                    'block_time': 3600
                }
                
                smart_logger.log_security_alert(
                    event_type="suspicious_activity",
                    details={
                        'ip': ip,
                        'user_agent': user_agent,
                        'indicators': suspicious_indicators,
                        'view': view_func.__name__
                    },
                    severity="medium"
                )
            
            # Aplicar rate limit normal
            return rate_limit(action, per_ip=True)(view_func)(request, *args, **kwargs)
        
        return wrapper
    return decorator


class RateLimitMiddleware:
    """Middleware global para rate limiting automático"""
    
    def __init__(self, get_response):
        self.get_response = get_response
        
        # Rutas que requieren rate limiting automático
        self.protected_paths = [
            '/accounts/login/',
            '/account/login/',
            '/registration/login/',
            '/accounts/password/reset/',
            '/accounts/signup/',
            '/api/',
        ]
    
    def __call__(self, request):
        # Verificar si la ruta está protegida
        path = request.path
        should_protect = any(path.startswith(protected_path) for protected_path in self.protected_paths)
        
        if should_protect and request.method == 'POST':
            ip = get_client_ip(request)
            
            # Determinar tipo de acción
            if 'login' in path:
                action = 'login'
            elif 'password' in path:
                action = 'password_reset'
            elif 'signup' in path:
                action = 'registration'
            elif 'api' in path:
                action = 'api_call'
            else:
                action = 'general'
            
            # Verificar rate limit
            allowed, attempts_left, reset_time = rate_limiter.check_rate_limit(action, f"ip:{ip}")
            
            if not allowed:
                remaining_time = rate_limiter.get_remaining_block_time(action, f"ip:{ip}")
                
                # Log del bloqueo
                smart_logger.log_security_alert(
                    event_type="middleware_rate_limit",
                    details={
                        'path': path,
                        'action': action,
                        'ip': ip,
                        'user_agent': get_user_agent(request),
                        'remaining_time': remaining_time
                    },
                    severity="medium"
                )
                
                # Respuesta de bloqueo
                if 'api' in path:
                    from django.http import JsonResponse
                    return JsonResponse({
                        'error': 'rate_limit_exceeded',
                        'message': f'Demasiados intentos. Intenta de nuevo en {remaining_time // 60} minutos.',
                        'retry_after': remaining_time
                    }, status=429)
                else:
                    context = {
                        'action': action,
                        'remaining_time': remaining_time,
                        'remaining_minutes': remaining_time // 60,
                        'path': path
                    }
                    return render(request, 'errors/rate_limit.html', context, status=429)
        
        response = self.get_response(request)
        return response
