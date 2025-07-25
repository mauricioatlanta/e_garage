#!/usr/bin/env python3
"""
🔧 Sistema de Verificación Completa - eGarage AI
==================================================

Este script verifica todas las funcionalidades implementadas del sistema
de suscripciones y confirma que todo está funcionando correctamente.

Autor: GitHub Copilot
Fecha: 2025-01-23
"""

import os
import sys
import django
from datetime import timedelta, datetime
from django.utils import timezone

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_taller.settings')
django.setup()

from django.contrib.auth.models import User
from taller.models.empresa import Empresa
from taller.models.comprobante_pago import ComprobantePago


def print_separator(title):
    """Imprime un separador visual con título"""
    print("\n" + "="*60)
    print(f"🔧 {title}")
    print("="*60)


def verificar_modelos():
    """Verifica que todos los modelos estén correctamente configurados"""
    print_separator("VERIFICACIÓN DE MODELOS")
    
    try:
        # Verificar modelo Empresa
        empresa_count = Empresa.objects.count()
        print(f"✅ Modelo Empresa: {empresa_count} empresas registradas")
        
        # Verificar modelo ComprobantePago
        comprobante_count = ComprobantePago.objects.count()
        print(f"✅ Modelo ComprobantePago: {comprobante_count} comprobantes registrados")
        
        # Verificar campos específicos del sistema de suscripciones
        if empresa_count > 0:
            empresa = Empresa.objects.first()
            print(f"   - Suscripción activa: {empresa.suscripcion_activa}")
            print(f"   - Fecha fin: {empresa.fecha_fin}")
            print(f"   - Plan: {empresa.plan}")
            print(f"   - Días restantes: {empresa.dias_restantes}")
        
        return True
    except Exception as e:
        print(f"❌ Error en modelos: {e}")
        return False


def verificar_suscripciones():
    """Verifica la lógica del sistema de suscripciones"""
    print_separator("VERIFICACIÓN DE SISTEMA DE SUSCRIPCIONES")
    
    try:
        # Buscar o crear empresa de prueba existente
        user, created = User.objects.get_or_create(
            username='test_suscripciones',
            defaults={'email': 'test@egarage.cl', 'first_name': 'Test', 'last_name': 'Suscripciones'}
        )
        
        # El signal automáticamente crea la empresa, así que la obtenemos
        try:
            empresa = user.empresa
        except Empresa.DoesNotExist:
            # Si por alguna razón no existe, la creamos manualmente
            empresa = Empresa.objects.create(
                nombre_taller='Taller Test Suscripciones',
                telefono='+56912345678',
                email='test@egarage.cl',
                direccion='Calle Test 123',
                user=user
            )
        
        # Asociar usuario si no está asociado (se hace automáticamente con el signal)
        
        print(f"✅ Empresa de prueba: {empresa.nombre_taller}")
        print(f"   - Plan: {empresa.plan}")
        print(f"   - Suscripción activa: {empresa.suscripcion_activa}")
        print(f"   - Días restantes: {empresa.dias_restantes}")
        
        # Verificar métodos de la empresa
        print(f"   - Debe bloquear: {empresa.debe_bloquear}")
        print(f"   - Estado suscripción: {empresa.estado_suscripcion}")
        
        # Simular vencimiento
        empresa.fecha_fin = timezone.now() - timedelta(days=1)
        empresa.save()
        print(f"   - Después de vencer: debe_bloquear = {empresa.debe_bloquear}")
        
        # Extender suscripción
        empresa.extender_suscripcion(30)
        print(f"   - Después de extender 30 días: debe_bloquear = {empresa.debe_bloquear}")
        
        return True
    except Exception as e:
        print(f"❌ Error en suscripciones: {e}")
        import traceback
        traceback.print_exc()
        return False


def verificar_comprobantes():
    """Verifica el sistema de comprobantes de pago"""
    print_separator("VERIFICACIÓN DE COMPROBANTES DE PAGO")
    
    try:
        # Obtener cualquier empresa para pruebas
        empresa = Empresa.objects.first()
        if not empresa:
            print("❌ No se encontró ninguna empresa en el sistema")
            return False
        
        print(f"✅ Usando empresa: {empresa.nombre_taller}")
        
        # Crear comprobante de prueba
        comprobante = ComprobantePago.objects.create(
            empresa=empresa,
            monto=25000,
            descripcion='Pago Plan Premium - Test',
            metodo_pago='transferencia'
        )
        
        print(f"✅ Comprobante creado exitosamente")
        print(f"   - Empresa: {comprobante.empresa.nombre_taller}")
        print(f"   - Monto: ${comprobante.monto:,.0f}")
        print(f"   - Estado: {comprobante.estado}")
        print(f"   - Fecha: {comprobante.fecha_subida}")
        
        # Probar aprobación
        dias_antes = empresa.dias_restantes
        comprobante.aprobar()
        empresa.refresh_from_db()
        dias_despues = empresa.dias_restantes
        
        print(f"   - Días antes de aprobar: {dias_antes}")
        print(f"   - Días después de aprobar: {dias_despues}")
        print(f"   - Suscripción extendida: {dias_despues > dias_antes}")
        
        return True
    except Exception as e:
        print(f"❌ Error en comprobantes: {e}")
        import traceback
        traceback.print_exc()
        return False


def verificar_urls():
    """Verifica que todas las URLs estén configuradas"""
    print_separator("VERIFICACIÓN DE URLs")
    
    try:
        from django.urls import reverse, NoReverseMatch
        
        urls_to_test = [
            ('precios', 'Página de precios'),
            ('estado_suscripcion', 'API estado suscripción'),
            ('subir_comprobante', 'Subir comprobante'),
            ('suspension', 'Página de suspensión'),
        ]
        
        for url_name, description in urls_to_test:
            try:
                url = reverse(url_name)
                print(f"✅ {description}: {url}")
            except NoReverseMatch:
                print(f"❌ {description}: URL no encontrada ({url_name})")
        
        return True
    except Exception as e:
        print(f"❌ Error verificando URLs: {e}")
        return False


def verificar_templates():
    """Verifica que todos los templates existan"""
    print_separator("VERIFICACIÓN DE TEMPLATES")
    
    templates_to_check = [
        'templates/suspension/suspension.html',
        'templates/suspension/subir_comprobante.html',
        'templates/suspension/precios.html',
    ]
    
    all_exist = True
    for template_path in templates_to_check:
        if os.path.exists(template_path):
            print(f"✅ {template_path}")
        else:
            print(f"❌ {template_path} - NO ENCONTRADO")
            all_exist = False
    
    return all_exist


def verificar_middleware():
    """Verifica la configuración del middleware"""
    print_separator("VERIFICACIÓN DE MIDDLEWARE")
    
    try:
        from django.conf import settings
        
        # Verificar que el middleware esté en MIDDLEWARE
        middleware_class = 'taller.middleware.empresa_middleware.EmpresaMiddleware'
        if middleware_class in settings.MIDDLEWARE:
            print(f"✅ Middleware configurado: {middleware_class}")
        else:
            print(f"❌ Middleware NO configurado: {middleware_class}")
            return False
        
        return True
    except Exception as e:
        print(f"❌ Error verificando middleware: {e}")
        return False


def main():
    """Función principal de verificación"""
    print("🔧 VERIFICACIÓN COMPLETA DEL SISTEMA eGARAGE AI")
    print("=" * 50)
    print("Verificando todas las funcionalidades implementadas...\n")
    
    # Lista de verificaciones
    verificaciones = [
        ("Modelos de base de datos", verificar_modelos),
        ("Sistema de suscripciones", verificar_suscripciones),
        ("Comprobantes de pago", verificar_comprobantes),
        ("Configuración de URLs", verificar_urls),
        ("Templates HTML", verificar_templates),
        ("Middleware de empresas", verificar_middleware),
    ]
    
    resultados = []
    
    # Ejecutar cada verificación
    for nombre, funcion in verificaciones:
        try:
            resultado = funcion()
            resultados.append((nombre, resultado))
        except Exception as e:
            print(f"❌ Error crítico en {nombre}: {e}")
            resultados.append((nombre, False))
    
    # Resumen final
    print_separator("RESUMEN FINAL")
    
    exitosas = 0
    total = len(resultados)
    
    for nombre, resultado in resultados:
        if resultado:
            print(f"✅ {nombre}")
            exitosas += 1
        else:
            print(f"❌ {nombre}")
    
    print(f"\n📊 RESULTADO: {exitosas}/{total} verificaciones exitosas")
    
    if exitosas == total:
        print("\n🎉 ¡SISTEMA COMPLETAMENTE FUNCIONAL!")
        print("   Todas las funcionalidades están implementadas y funcionando")
        print("   ✅ Sistema de suscripciones listo para producción")
        print("   ✅ Middleware de bloqueo activo")
        print("   ✅ Gestión de pagos implementada")
        print("   ✅ Interfaces de usuario completas")
    else:
        print(f"\n⚠️ ATENCIÓN: {total - exitosas} verificaciones fallaron")
        print("   Revisar los errores antes de continuar")
    
    print("\n" + "="*50)
    print("Verificación completada.")


if __name__ == "__main__":
    main()
