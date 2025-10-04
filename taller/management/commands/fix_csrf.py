#!/usr/bin/env python
"""
Comando Django para limpiar tokens CSRF y sesiones problemáticas.
"""
from django.core.management.base import BaseCommand
from django.contrib.sessions.models import Session
from django.core.cache import cache
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Limpia tokens CSRF y sesiones para resolver problemas de autenticación'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Forzar limpieza incluso si no hay problemas detectados',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('🔧 Iniciando limpieza de CSRF y sesiones...'))
        
        # 1. Limpiar todas las sesiones
        self.stdout.write('📝 Limpiando sesiones...')
        try:
            sessions_deleted, _ = Session.objects.all().delete()
            self.stdout.write(self.style.SUCCESS(f'  ✅ Sesiones eliminadas: {sessions_deleted}'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'  ❌ Error limpiando sesiones: {e}'))

        # 2. Limpiar caché CSRF
        self.stdout.write('🗑️ Limpiando caché CSRF...')
        try:
            # Limpiar caché general
            cache.clear()
            self.stdout.write(self.style.SUCCESS('  ✅ Caché limpiado'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'  ❌ Error limpiando caché: {e}'))

        # 3. Mostrar configuraciones CSRF actuales
        self.stdout.write('⚙️ Configuraciones CSRF actuales:')
        self.stdout.write(f'  - DEBUG: {settings.DEBUG}')
        self.stdout.write(f'  - CSRF_COOKIE_HTTPONLY: {getattr(settings, "CSRF_COOKIE_HTTPONLY", "No definido")}')
        self.stdout.write(f'  - CSRF_COOKIE_SAMESITE: {getattr(settings, "CSRF_COOKIE_SAMESITE", "No definido")}')
        self.stdout.write(f'  - CSRF_USE_SESSIONS: {getattr(settings, "CSRF_USE_SESSIONS", "No definido")}')
        
        # Mostrar CSRF_TRUSTED_ORIGINS
        trusted_origins = getattr(settings, 'CSRF_TRUSTED_ORIGINS', [])
        self.stdout.write(f'  - CSRF_TRUSTED_ORIGINS: {trusted_origins}')

        # 4. Verificar middleware CSRF
        self.stdout.write('🛡️ Verificando middleware CSRF...')
        csrf_middleware = 'django.middleware.csrf.CsrfViewMiddleware'
        if csrf_middleware in settings.MIDDLEWARE:
            self.stdout.write(self.style.SUCCESS(f'  ✅ {csrf_middleware} está activo'))
        else:
            self.stdout.write(self.style.ERROR(f'  ❌ {csrf_middleware} NO está en MIDDLEWARE'))

        # 5. Recomendaciones
        self.stdout.write('')
        self.stdout.write(self.style.WARNING('💡 Recomendaciones:'))
        self.stdout.write('  1. Cierra todas las pestañas del navegador')
        self.stdout.write('  2. Limpia las cookies del sitio')
        self.stdout.write('  3. Reinicia el servidor Django')
        self.stdout.write('  4. Haz login nuevamente')
        
        if settings.DEBUG:
            self.stdout.write('')
            self.stdout.write(self.style.WARNING('🐛 Para DEBUG=True:'))
            self.stdout.write('  - Verifica que estés usando http://127.0.0.1:8000')
            self.stdout.write('  - No uses https:// en desarrollo')
            self.stdout.write('  - Asegúrate de que CSRF_TRUSTED_ORIGINS incluya tu URL')

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('✅ Limpieza completada. Reinicia el servidor y prueba nuevamente.'))
