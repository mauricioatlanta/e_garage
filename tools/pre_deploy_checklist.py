#!/usr/bin/env python
"""
Checklist de Pre-Despliegue a Producción para eGarage Django
Incluye: Seguridad, Estáticos, DB, Logging, Verificación y Plan de Rollback
"""

import os
import sys
import django
from django.conf import settings
from django.core.management import execute_from_command_line
from django.test import Client
from django.contrib.auth import get_user_model

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_taller.settings.dev')
django.setup()

User = get_user_model()

def check_security_settings():
    """Verificar configuraciones de seguridad"""
    print("🔒 VERIFICANDO CONFIGURACIONES DE SEGURIDAD")
    print("=" * 50)
    
    issues = []
    
    # DEBUG
    if settings.DEBUG:
        issues.append("❌ DEBUG=True (debe ser False en producción)")
    else:
        print("✅ DEBUG=False")
    
    # ALLOWED_HOSTS
    if not settings.ALLOWED_HOSTS or settings.ALLOWED_HOSTS == ['*']:
        issues.append("❌ ALLOWED_HOSTS no configurado correctamente")
    else:
        print(f"✅ ALLOWED_HOSTS: {settings.ALLOWED_HOSTS}")
    
    # SECRET_KEY
    if not settings.SECRET_KEY or settings.SECRET_KEY == 'your-secret-key-here':
        issues.append("❌ SECRET_KEY no configurado")
    else:
        print("✅ SECRET_KEY configurado")
    
    # CSRF_TRUSTED_ORIGINS
    if hasattr(settings, 'CSRF_TRUSTED_ORIGINS'):
        print(f"✅ CSRF_TRUSTED_ORIGINS: {settings.CSRF_TRUSTED_ORIGINS}")
    else:
        issues.append("⚠️  CSRF_TRUSTED_ORIGINS no configurado")
    
    # Cookies seguras
    secure_cookies = [
        ('SESSION_COOKIE_SECURE', 'SESSION_COOKIE_SECURE'),
        ('CSRF_COOKIE_SECURE', 'CSRF_COOKIE_SECURE'),
        ('SECURE_SSL_REDIRECT', 'SECURE_SSL_REDIRECT'),
    ]
    
    for attr, name in secure_cookies:
        if hasattr(settings, attr):
            value = getattr(settings, attr)
            if value:
                print(f"✅ {name}=True")
            else:
                issues.append(f"⚠️  {name}=False (recomendado para producción)")
        else:
            issues.append(f"⚠️  {name} no configurado")
    
    if issues:
        print("\n⚠️  PROBLEMAS DE SEGURIDAD ENCONTRADOS:")
        for issue in issues:
            print(f"   {issue}")
    else:
        print("\n✅ TODAS LAS CONFIGURACIONES DE SEGURIDAD OK")
    
    return len(issues) == 0

def check_static_files():
    """Verificar archivos estáticos"""
    print("\n📁 VERIFICANDO ARCHIVOS ESTÁTICOS")
    print("=" * 50)
    
    issues = []
    
    # WhiteNoise
    if hasattr(settings, 'STATICFILES_STORAGE'):
        if 'whitenoise' in settings.STATICFILES_STORAGE:
            print("✅ WhiteNoise configurado")
        else:
            issues.append("⚠️  WhiteNoise no configurado")
    else:
        issues.append("❌ STATICFILES_STORAGE no configurado")
    
    # Middleware
    if 'whitenoise.middleware.WhiteNoiseMiddleware' in settings.MIDDLEWARE:
        print("✅ WhiteNoise middleware configurado")
    else:
        issues.append("❌ WhiteNoise middleware no encontrado")
    
    # STATIC_ROOT
    if hasattr(settings, 'STATIC_ROOT') and settings.STATIC_ROOT:
        print(f"✅ STATIC_ROOT: {settings.STATIC_ROOT}")
    else:
        issues.append("❌ STATIC_ROOT no configurado")
    
    # Verificar archivos críticos
    critical_files = [
        'static/taller/common/js/documentos_form.js',
        'static/taller/common/css/',
    ]
    
    for file_path in critical_files:
        if os.path.exists(file_path):
            print(f"✅ {file_path} existe")
        else:
            issues.append(f"❌ {file_path} no encontrado")
    
    if issues:
        print("\n⚠️  PROBLEMAS CON ARCHIVOS ESTÁTICOS:")
        for issue in issues:
            print(f"   {issue}")
    else:
        print("\n✅ ARCHIVOS ESTÁTICOS OK")
    
    return len(issues) == 0

def check_database():
    """Verificar base de datos"""
    print("\n🗄️  VERIFICANDO BASE DE DATOS")
    print("=" * 50)
    
    issues = []
    
    try:
        from django.db import connection
        cursor = connection.cursor()
        cursor.execute("SELECT 1")
        print("✅ Conexión a base de datos OK")
    except Exception as e:
        issues.append(f"❌ Error de conexión DB: {e}")
    
    # Verificar migraciones pendientes
    try:
        from django.core.management import call_command
        from io import StringIO
        
        out = StringIO()
        call_command('showmigrations', 'taller', stdout=out)
        output = out.getvalue()
        
        if '[ ]' in output:
            issues.append("⚠️  Migraciones pendientes detectadas")
        else:
            print("✅ Todas las migraciones aplicadas")
    except Exception as e:
        issues.append(f"⚠️  No se pudo verificar migraciones: {e}")
    
    # Verificar modelos críticos
    try:
        from taller.models import Documento, Empresa, Cliente, Vehiculo
        
        doc_count = Documento.objects.count()
        emp_count = Empresa.objects.count()
        cli_count = Cliente.objects.count()
        veh_count = Vehiculo.objects.count()
        
        print(f"✅ Documentos: {doc_count}")
        print(f"✅ Empresas: {emp_count}")
        print(f"✅ Clientes: {cli_count}")
        print(f"✅ Vehículos: {veh_count}")
        
    except Exception as e:
        issues.append(f"❌ Error accediendo a modelos: {e}")
    
    if issues:
        print("\n⚠️  PROBLEMAS CON BASE DE DATOS:")
        for issue in issues:
            print(f"   {issue}")
    else:
        print("\n✅ BASE DE DATOS OK")
    
    return len(issues) == 0

def check_logging():
    """Verificar configuración de logging"""
    print("\n📝 VERIFICANDO LOGGING")
    print("=" * 50)
    
    issues = []
    
    if hasattr(settings, 'LOGGING'):
        print("✅ LOGGING configurado")
        
        # Verificar nivel
        if 'root' in settings.LOGGING and 'level' in settings.LOGGING['root']:
            level = settings.LOGGING['root']['level']
            print(f"✅ Nivel de logging: {level}")
        else:
            issues.append("⚠️  Nivel de logging no configurado")
    else:
        issues.append("❌ LOGGING no configurado")
    
    # Verificar Sentry (opcional)
    if hasattr(settings, 'SENTRY_DSN'):
        print("✅ Sentry configurado")
    else:
        print("ℹ️  Sentry no configurado (opcional)")
    
    if issues:
        print("\n⚠️  PROBLEMAS CON LOGGING:")
        for issue in issues:
            print(f"   {issue}")
    else:
        print("\n✅ LOGGING OK")
    
    return len(issues) == 0

def smoke_test():
    """Smoke test funcional"""
    print("\n🧪 SMOKE TEST FUNCIONAL")
    print("=" * 50)
    
    issues = []
    client = Client()
    
    # Test Chile
    print("\n🇨🇱 Testing Chile (CLP + IVA 19%)")
    try:
        login_success = client.login(username='test_chile', password='test123')
        if login_success:
            print("✅ Login CL exitoso")
            response = client.get('/cl/es/documentos/form/')
            if response.status_code == 200:
                print("✅ Formulario CL carga correctamente")
            else:
                issues.append(f"❌ Formulario CL error: {response.status_code}")
        else:
            issues.append("❌ Login CL falló")
    except Exception as e:
        issues.append(f"❌ Error en test CL: {e}")
    
    # Test USA
    print("\n🇺🇸 Testing USA (USD + Sales Tax 0%)")
    try:
        login_success = client.login(username='testuser_usa', password='TestUSA2025!')
        if login_success:
            print("✅ Login US exitoso")
            response = client.get('/us/en/documentos/form/')
            if response.status_code == 200:
                print("✅ Formulario US carga correctamente")
            else:
                issues.append(f"❌ Formulario US error: {response.status_code}")
        else:
            issues.append("❌ Login US falló")
    except Exception as e:
        issues.append(f"❌ Error en test US: {e}")
    
    # Test JavaScript
    print("\n📜 Testing JavaScript")
    try:
        response = client.get('/static/taller/common/js/documentos_form.js')
        if response.status_code == 200:
            print("✅ JavaScript carga correctamente")
            content = response.content.decode('utf-8')
            if 'recalcTotals' in content:
                print("✅ Función recalcTotals encontrada")
            if 'VAT_PCT' in content:
                print("✅ Variable VAT_PCT encontrada")
        else:
            issues.append(f"❌ JavaScript error: {response.status_code}")
    except Exception as e:
        issues.append(f"❌ Error en test JS: {e}")
    
    if issues:
        print("\n⚠️  PROBLEMAS EN SMOKE TEST:")
        for issue in issues:
            print(f"   {issue}")
    else:
        print("\n✅ SMOKE TEST OK")
    
    return len(issues) == 0

def generate_production_settings():
    """Generar configuración de producción"""
    print("\n⚙️  GENERANDO CONFIGURACIÓN DE PRODUCCIÓN")
    print("=" * 50)
    
    production_settings = '''
# Configuración de Producción para eGarage
# Archivo: gestion_taller/settings/production.py

import os
from .base import *

# Debug deshabilitado
DEBUG = False

# Hosts permitidos (ajustar según tu dominio)
ALLOWED_HOSTS = [
    "yourdomain.com",
    "www.yourdomain.com", 
    "127.0.0.1",
    "localhost"
]

# Orígenes CSRF confiables
CSRF_TRUSTED_ORIGINS = [
    "https://yourdomain.com",
    "https://www.yourdomain.com"
]

# Cookies seguras
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_SSL_REDIRECT = True
SECURE_HSTS_SECONDS = 31536000  # 1 año
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# Base de datos PostgreSQL
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('DB_NAME', 'egarage_prod'),
        'USER': os.getenv('DB_USER', 'egarage_user'),
        'PASSWORD': os.getenv('DB_PASSWORD'),
        'HOST': os.getenv('DB_HOST', 'localhost'),
        'PORT': os.getenv('DB_PORT', '5432'),
        'CONN_MAX_AGE': 60,
    }
}

# Archivos estáticos con WhiteNoise
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

# Logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
}

# Sentry (opcional)
if os.getenv('SENTRY_DSN'):
    import sentry_sdk
    from sentry_sdk.integrations.django import DjangoIntegration
    
    sentry_sdk.init(
        dsn=os.getenv('SENTRY_DSN'),
        integrations=[DjangoIntegration()],
        traces_sample_rate=0.1,
        send_default_pii=True
    )

# Timezone
TIME_ZONE = "America/Santiago"
USE_TZ = True
LANGUAGE_CODE = "es-cl"
'''
    
    with open('gestion_taller/settings/production_template.py', 'w', encoding='utf-8') as f:
        f.write(production_settings)
    
    print("✅ Archivo de configuración de producción generado:")
    print("   gestion_taller/settings/production_template.py")

def generate_deployment_commands():
    """Generar comandos de despliegue"""
    print("\n🚀 COMANDOS DE DESPLIEGUE")
    print("=" * 50)
    
    commands = '''
# Comandos de Despliegue para eGarage

## 1. Variables de Entorno (configurar en servidor)
export DJANGO_SETTINGS_MODULE="gestion_taller.settings.production"
export DEBUG="False"
export SECRET_KEY="your-secret-key-here"
export DATABASE_URL="postgres://user:password@host:port/dbname"
export ALLOWED_HOSTS="yourdomain.com,www.yourdomain.com"
export CSRF_TRUSTED_ORIGINS="https://yourdomain.com,https://www.yourdomain.com"

## 2. Migraciones y Estáticos
python manage.py migrate
python manage.py collectstatic --noinput

## 3. Verificación
python manage.py shell -c "from django.conf import settings; print('DEBUG=', settings.DEBUG)"

## 4. Gunicorn (Render)
gunicorn gestion_taller.wsgi:application --workers 3 --timeout 120 --bind 0.0.0.0:8000

## 5. Health Check
curl http://localhost:8000/health/

## 6. Post-Deploy Checklist
# - Crear documento en /cl/ y /us/
# - Verificar totales en admin
# - Revisar logs
# - Probar correo (si aplica)
'''
    
    with open('tools/deployment_commands.md', 'w', encoding='utf-8') as f:
        f.write(commands)
    
    print("✅ Comandos de despliegue generados:")
    print("   tools/deployment_commands.md")

def main():
    """Ejecutar checklist completo"""
    print("🎯 CHECKLIST DE PRE-DESPLIEGUE A PRODUCCIÓN")
    print("=" * 60)
    print("eGarage Django - Verificación completa")
    print("=" * 60)
    
    results = []
    
    # Ejecutar verificaciones
    results.append(("Seguridad", check_security_settings()))
    results.append(("Archivos Estáticos", check_static_files()))
    results.append(("Base de Datos", check_database()))
    results.append(("Logging", check_logging()))
    results.append(("Smoke Test", smoke_test()))
    
    # Generar archivos de configuración
    generate_production_settings()
    generate_deployment_commands()
    
    # Resumen final
    print("\n📊 RESUMEN FINAL")
    print("=" * 50)
    
    passed = 0
    total = len(results)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{name:20} {status}")
        if result:
            passed += 1
    
    print(f"\nResultado: {passed}/{total} verificaciones pasaron")
    
    if passed == total:
        print("\n🎉 ¡SISTEMA LISTO PARA PRODUCCIÓN!")
        print("✅ Todas las verificaciones pasaron")
        print("✅ Archivos de configuración generados")
        print("✅ Comandos de despliegue listos")
    else:
        print(f"\n⚠️  {total - passed} problemas encontrados")
        print("❌ Revisar y corregir antes del despliegue")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
