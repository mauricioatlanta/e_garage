#!/usr/bin/env python
"""
Test de mejoras del modelo Empresa refinado
"""

import os
import sys
import django
from django.conf import settings

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_taller.settings')
django.setup()

from datetime import timedelta
from decimal import Decimal
from taller.models.empresa import Empresa
from django.utils import timezone


def test_dias_restantes_ceil():
    """Prueba el cálculo de días restantes con ceil"""
    
    print("📅 TEST DE DÍAS RESTANTES CON CEIL")
    print("=" * 60)
    
    # Crear empresa de prueba
    empresa = Empresa.objects.first()
    if not empresa:
        print("❌ No se encontró empresa para la prueba")
        return
    
    # Simular que faltan 1.9 días (debería mostrar 2 con ceil)
    ahora = timezone.now()
    empresa.fecha_fin = ahora + timedelta(days=1, hours=21, minutes=30)  # 1.9 días
    empresa.save()
    
    print(f"Fecha fin: {empresa.fecha_fin}")
    print(f"Días restantes (con ceil): {empresa.dias_restantes}")
    
    # Verificar que usa ceil
    if empresa.dias_restantes == 2:
        print("✅ Ceil funcionando correctamente")
    else:
        print(f"❌ Ceil no funcionó. Esperado: 2, Obtenido: {empresa.dias_restantes}")


def test_tz_autocorrect_por_pais():
    """Prueba la auto-corrección de zona horaria por país"""
    
    print("\n🌍 TEST DE AUTO-CORRECCIÓN DE ZONA HORARIA")
    print("=" * 60)
    
    # Crear empresa de prueba
    empresa = Empresa.objects.first()
    if not empresa:
        print("❌ No se encontró empresa para la prueba")
        return
    
    # Test 1: Empresa USA con zona horaria inválida
    print("\n1️⃣ Empresa USA con zona horaria inválida:")
    empresa.pais = "US"
    empresa.zona_horaria = "America/Santiago"  # Zona de Chile
    empresa.save()
    
    print(f"   Zona horaria después de save: {empresa.zona_horaria}")
    if empresa.zona_horaria in empresa.US_TZS:
        print("✅ Zona horaria corregida correctamente")
    else:
        print("❌ Zona horaria no fue corregida")
    
    # Test 2: Empresa Chile con zona horaria válida (no debe cambiar)
    print("\n2️⃣ Empresa Chile con zona horaria válida:")
    empresa.pais = "CL"
    zona_original = "America/Santiago"
    empresa.zona_horaria = zona_original
    empresa.save()
    
    print(f"   Zona horaria después de save: {empresa.zona_horaria}")
    if empresa.zona_horaria == zona_original:
        print("✅ Zona horaria válida no fue modificada")
    else:
        print("❌ Zona horaria válida fue modificada incorrectamente")


def test_estado_y_color_suscripcion():
    """Prueba los estados y colores de suscripción"""
    
    print("\n🎨 TEST DE ESTADOS Y COLORES DE SUSCRIPCIÓN")
    print("=" * 60)
    
    # Crear empresa de prueba
    empresa = Empresa.objects.first()
    if not empresa:
        print("❌ No se encontró empresa para la prueba")
        return
    
    # Test 1: Estado activa
    print("\n1️⃣ Estado activa:")
    empresa.fecha_fin = timezone.now() + timedelta(days=10)
    empresa.suscripcion_activa = True
    empresa.save()
    
    print(f"   Días restantes: {empresa.dias_restantes}")
    print(f"   Estado: {empresa.estado_suscripcion}")
    print(f"   Color: {empresa.color_estado}")
    
    # Test 2: Estado advertencia
    print("\n2️⃣ Estado advertencia:")
    empresa.fecha_fin = timezone.now() + timedelta(days=3)
    empresa.save()
    
    print(f"   Días restantes: {empresa.dias_restantes}")
    print(f"   Estado: {empresa.estado_suscripcion}")
    print(f"   Color: {empresa.color_estado}")
    
    # Test 3: Estado crítico
    print("\n3️⃣ Estado crítico:")
    empresa.fecha_fin = timezone.now() + timedelta(hours=12)
    empresa.save()
    
    print(f"   Días restantes: {empresa.dias_restantes}")
    print(f"   Estado: {empresa.estado_suscripcion}")
    print(f"   Color: {empresa.color_estado}")
    
    # Test 4: Estado vencida
    print("\n4️⃣ Estado vencida:")
    empresa.fecha_fin = timezone.now() - timedelta(days=1)
    empresa.suscripcion_activa = False
    empresa.save()
    
    print(f"   Días restantes: {empresa.dias_restantes}")
    print(f"   Estado: {empresa.estado_suscripcion}")
    print(f"   Color: {empresa.color_estado}")


def test_extender_suscripcion():
    """Prueba la extensión de suscripción"""
    
    print("\n💰 TEST DE EXTENSIÓN DE SUSCRIPCIÓN")
    print("=" * 60)
    
    # Crear empresa de prueba
    empresa = Empresa.objects.first()
    if not empresa:
        print("❌ No se encontró empresa para la prueba")
        return
    
    # Test 1: Extender suscripción activa
    print("\n1️⃣ Extender suscripción activa:")
    fecha_fin_original = timezone.now() + timedelta(days=5)
    empresa.fecha_fin = fecha_fin_original
    empresa.suscripcion_activa = True
    empresa.save()
    
    print(f"   Fecha fin original: {fecha_fin_original}")
    
    empresa.extender_suscripcion(30)
    
    print(f"   Fecha fin después de extender: {empresa.fecha_fin}")
    print(f"   Suscripción activa: {empresa.suscripcion_activa}")
    print(f"   Notificaciones reseteadas: {not empresa.notificacion_5_dias}")
    
    # Test 2: Extender suscripción vencida
    print("\n2️⃣ Extender suscripción vencida:")
    empresa.fecha_fin = timezone.now() - timedelta(days=1)
    empresa.suscripcion_activa = False
    empresa.save()
    
    print(f"   Fecha fin original (vencida): {empresa.fecha_fin}")
    
    empresa.extender_suscripcion(30)
    
    print(f"   Fecha fin después de extender: {empresa.fecha_fin}")
    print(f"   Suscripción activa: {empresa.suscripcion_activa}")


def test_moneda_y_formato():
    """Prueba la gestión de moneda y formato"""
    
    print("\n💱 TEST DE MONEDA Y FORMATO")
    print("=" * 60)
    
    # Test 1: Empresa USA
    print("\n1️⃣ Empresa USA:")
    empresa_usa = Empresa.objects.filter(pais="US").first()
    if empresa_usa:
        print(f"   País: {empresa_usa.pais}")
        print(f"   Moneda: {empresa_usa.moneda}")
        print(f"   Símbolo: {empresa_usa.simbolo_moneda}")
        print(f"   Formato: {empresa_usa.formato_moneda}")
    else:
        print("   ⚠️ No hay empresa USA para probar")
    
    # Test 2: Empresa Chile
    print("\n2️⃣ Empresa Chile:")
    empresa_chile = Empresa.objects.filter(pais="CL").first()
    if empresa_chile:
        print(f"   País: {empresa_chile.pais}")
        print(f"   Moneda: {empresa_chile.moneda}")
        print(f"   Símbolo: {empresa_chile.simbolo_moneda}")
        print(f"   Formato: {empresa_chile.formato_moneda}")
    else:
        print("   ⚠️ No hay empresa Chile para probar")


def test_mensajes_alerta():
    """Prueba los mensajes de alerta"""
    
    print("\n⚠️ TEST DE MENSAJES DE ALERTA")
    print("=" * 60)
    
    # Crear empresa de prueba
    empresa = Empresa.objects.first()
    if not empresa:
        print("❌ No se encontró empresa para la prueba")
        return
    
    # Test diferentes escenarios
    escenarios = [
        ("Vencida", timezone.now() - timedelta(days=1), False),
        ("Crítica (1 día)", timezone.now() + timedelta(hours=12), True),
        ("Advertencia (3 días)", timezone.now() + timedelta(days=3), True),
        ("Activa (10 días)", timezone.now() + timedelta(days=10), True),
    ]
    
    for nombre, fecha_fin, activa in escenarios:
        print(f"\n{nombre}:")
        empresa.fecha_fin = fecha_fin
        empresa.suscripcion_activa = activa
        empresa.save()
        
        print(f"   Días restantes: {empresa.dias_restantes}")
        print(f"   Debe mostrar alerta: {empresa.debe_mostrar_alerta()}")
        mensaje = empresa.get_mensaje_alerta()
        if mensaje:
            print(f"   Mensaje: {mensaje}")
        else:
            print("   Sin mensaje de alerta")


if __name__ == "__main__":
    test_dias_restantes_ceil()
    test_tz_autocorrect_por_pais()
    test_estado_y_color_suscripcion()
    test_extender_suscripcion()
    test_moneda_y_formato()
    test_mensajes_alerta()
