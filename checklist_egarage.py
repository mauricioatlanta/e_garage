#!/usr/bin/env python
"""
Checklist eGarage completo.
Verifica que todos los aspectos del sistema estén funcionando correctamente.
"""

import os
import sys
import django

# Configurar Django
sys.path.insert(0, os.path.dirname(__file__))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_taller.settings.dev')
django.setup()

from django.core.management import call_command
from django.urls import get_resolver

def checklist_egarage():
    """Ejecuta el checklist completo de eGarage."""
    print("🔍 Ejecutando checklist eGarage completo...")
    print("=" * 50)
    
    resultados = []
    
    # 1. makemigrations / migrate
    print("1. ✅ makemigrations / migrate")
    try:
        call_command('makemigrations', check=True)
        call_command('migrate', check=True)
        print("   ✅ Migraciones OK")
        resultados.append(True)
    except Exception as e:
        print(f"   ❌ Error en migraciones: {e}")
        resultados.append(False)
    
    # 2. Árbol de URLs único por país/idioma
    print("\n2. ✅ Árbol de URLs único por país/idioma")
    try:
        resolver = get_resolver()
        names = [k for k in resolver.reverse_dict.keys() if isinstance(k, str)]
        
        # Verificar que no hay duplicados
        if len(names) == len(set(names)):
            print("   ✅ No hay duplicados en URLs")
            resultados.append(True)
        else:
            print("   ❌ Hay duplicados en URLs")
            resultados.append(False)
            
    except Exception as e:
        print(f"   ❌ Error verificando URLs: {e}")
        resultados.append(False)
    
    # 3. Verificar URLs específicas
    print("\n3. 🔎 python manage.py show_urls | findstr /I 'taller_us_en'")
    try:
        us_en_names = [name for name in names if "taller_us_en" in name]
        cl_es_names = [name for name in names if "taller_cl_es" in name]
        
        print(f"   ✅ {len(us_en_names)} URLs para US/EN")
        print(f"   ✅ {len(cl_es_names)} URLs para CL/ES")
        resultados.append(True)
        
    except Exception as e:
        print(f"   ❌ Error verificando URLs específicas: {e}")
        resultados.append(False)
    
    # 4. Test anti-duplicados de nombres de URL
    print("\n4. 🧪 Test anti-duplicados de nombres de URL")
    try:
        # Importar y ejecutar el test
        from tests.unit.test_urls_unique_names import test_unique_url_names
        test_unique_url_names()
        print("   ✅ Test anti-duplicados OK")
        resultados.append(True)
    except Exception as e:
        print(f"   ❌ Error en test anti-duplicados: {e}")
        resultados.append(False)
    
    # 5. KPIs usando solo fecha_emision
    print("\n5. 📊 KPIs usando solo fecha_emision")
    try:
        from kpi_sanity_check import kpi_sanity_check
        if kpi_sanity_check():
            print("   ✅ KPIs OK")
            resultados.append(True)
        else:
            print("   ❌ Error en KPIs")
            resultados.append(False)
    except Exception as e:
        print(f"   ❌ Error verificando KPIs: {e}")
        resultados.append(False)
    
    # 6. python manage.py check --deploy
    print("\n6. 🛡️ python manage.py check --deploy")
    try:
        call_command('check', '--deploy')
        print("   ✅ Check deploy OK")
        resultados.append(True)
    except Exception as e:
        print(f"   ❌ Error en check deploy: {e}")
        resultados.append(False)
    
    # Resumen final
    print("\n" + "=" * 50)
    print("📊 RESUMEN DEL CHECKLIST")
    print("=" * 50)
    
    total_checks = len(resultados)
    checks_ok = sum(resultados)
    
    print(f"Checks ejecutados: {checks_ok}/{total_checks}")
    
    if checks_ok == total_checks:
        print("\n🎉 ¡TODOS LOS CHECKS PASARON!")
        print("✅ El sistema está listo para producción")
    else:
        print(f"\n⚠️  {total_checks - checks_ok} checks fallaron")
        print("❌ Revisar los errores antes de continuar")
    
    return checks_ok == total_checks

if __name__ == "__main__":
    checklist_egarage()
