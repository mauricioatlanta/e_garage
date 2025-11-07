#!/usr/bin/env python3
"""
Script para ejecutar las pruebas backend de documentos
Ejecutar con: python tools/run_backend_tests.py
"""

import os
import sys
import django
from django.conf import settings
from django.test.utils import get_runner

def setup_django():
    """Configurar Django para las pruebas"""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_taller.settings')
    django.setup()

def run_tests():
    """Ejecutar las pruebas backend"""
    print("🧪 EJECUTANDO PRUEBAS BACKEND DE DOCUMENTOS")
    print("=" * 60)
    
    # Configurar Django
    setup_django()
    
    # Obtener el test runner
    TestRunner = get_runner(settings)
    test_runner = TestRunner()
    
    # Ejecutar las pruebas
    print("\n🚀 Iniciando pruebas...")
    failures = test_runner.run_tests(["tests.test_documento_backend"])
    
    # Mostrar resultados
    print("\n" + "=" * 60)
    print("📊 RESULTADOS DE LAS PRUEBAS")
    print("=" * 60)
    
    if failures:
        print(f"❌ {failures} pruebas fallaron")
        print("🔧 Revisar los errores anteriores")
        return False
    else:
        print("✅ Todas las pruebas pasaron")
        print("🎉 El backend está funcionando correctamente")
        return True

if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
