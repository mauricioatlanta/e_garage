# ===============================================================
# 🚀 SCRIPT DE ACTUALIZACIÓN PARA PYTHONANYWHERE
# ===============================================================
# Archivos que necesitas subir para arreglar el error 404
# ===============================================================

import os
import shutil
from datetime import datetime

def crear_paquete_actualizacion():
    """Crear paquete con archivos actualizados"""
    print("📦 CREANDO PAQUETE DE ACTUALIZACIÓN PARA PYTHONANYWHERE")
    print("=" * 60)
    
    # Crear directorio de actualización
    update_dir = "actualizacion_pythonanywhere"
    if os.path.exists(update_dir):
        shutil.rmtree(update_dir)
    os.makedirs(update_dir, exist_ok=True)
    
    # Archivos que necesitan subirse
    archivos_actualizar = [
        {
            'origen': 'gestion_taller/urls.py',
            'destino': f'{update_dir}/gestion_taller_urls.py',
            'descripcion': 'URLs principales con rutas de bienvenida'
        },
        {
            'origen': 'templates/onboarding/bienvenida_chile.html',
            'destino': f'{update_dir}/bienvenida_chile.html',
            'descripcion': 'Plantilla de bienvenida para Chile'
        },
        {
            'origen': 'templates/onboarding/bienvenida_usa.html',
            'destino': f'{update_dir}/bienvenida_usa.html',
            'descripcion': 'Plantilla de bienvenida para USA'
        }
    ]
    
    print("📋 ARCHIVOS A ACTUALIZAR:")
    for archivo in archivos_actualizar:
        if os.path.exists(archivo['origen']):
            # Copiar archivo
            os.makedirs(os.path.dirname(archivo['destino']), exist_ok=True)
            shutil.copy2(archivo['origen'], archivo['destino'])
            print(f"✅ {archivo['descripcion']}")
            print(f"   📂 {archivo['origen']} → {archivo['destino']}")
        else:
            print(f"❌ {archivo['origen']} - NO ENCONTRADO")
    
    return update_dir

def generar_instrucciones_deploy():
    """Generar instrucciones paso a paso"""
    instrucciones = """
# ===============================================================
# 🚀 INSTRUCCIONES DE ACTUALIZACIÓN PARA PYTHONANYWHERE
# ===============================================================

## 🎯 PROBLEMA IDENTIFICADO:
El error 404 en /bienvenida/usa/ se debe a que las URLs nuevas 
no están en el servidor de producción.

## 📦 ARCHIVOS A SUBIR:

### 1. 📂 gestion_taller/urls.py (ACTUALIZAR)
   - Contiene las nuevas rutas de bienvenida
   - Reemplazar el archivo existente en el servidor

### 2. 📂 templates/onboarding/bienvenida_chile.html (NUEVO)
   - Plantilla para la página de bienvenida de Chile
   - Crear en: /templates/onboarding/

### 3. 📂 templates/onboarding/bienvenida_usa.html (NUEVO)
   - Plantilla para la página de bienvenida de USA
   - Crear en: /templates/onboarding/

## 🚀 PASOS DE ACTUALIZACIÓN:

### PASO 1: Subir archivos via Files
1. Ir a "Files" en PythonAnywhere
2. Navegar a: /home/atlantareciclajes/e-garage-atlantareciclajes/
3. Subir y reemplazar: gestion_taller/urls.py
4. Crear directorio: templates/onboarding/ (si no existe)
5. Subir: bienvenida_chile.html y bienvenida_usa.html

### PASO 2: Recargar aplicación web
1. Ir al tab "Web"
2. Hacer clic en "Reload atlantareciclajes.pythonanywhere.com"

### PASO 3: Verificar URLs
Probar estos enlaces:
✅ https://e-garage-atlantareciclajes.pythonanywhere.com/bienvenida/cl/
✅ https://e-garage-atlantareciclajes.pythonanywhere.com/bienvenida/usa/
✅ https://e-garage-atlantareciclajes.pythonanywhere.com/welcome/us/

## 🎉 RESULTADO ESPERADO:
Después de estos pasos, las URLs de bienvenida funcionarán correctamente.

## 📞 SOPORTE:
Si hay problemas, verificar en "Error log" del tab Web.
"""
    
    with open('actualizacion_pythonanywhere/INSTRUCCIONES_DEPLOY.md', 'w', encoding='utf-8') as f:
        f.write(instrucciones)
    
    print("\n📝 INSTRUCCIONES GENERADAS:")
    print("   📄 actualizacion_pythonanywhere/INSTRUCCIONES_DEPLOY.md")

def mostrar_resumen():
    """Mostrar resumen de la actualización"""
    print("\n" + "=" * 60)
    print("📋 RESUMEN DE LA ACTUALIZACIÓN")
    print("=" * 60)
    
    print("🔍 PROBLEMA:")
    print("   Las URLs /bienvenida/usa/ y /bienvenida/cl/ causan error 404")
    print("   porque no están en el servidor de producción.")
    
    print("\n🛠️  SOLUCIÓN:")
    print("   1. Subir gestion_taller/urls.py actualizado")
    print("   2. Subir plantillas HTML de bienvenida")
    print("   3. Recargar aplicación web en PythonAnywhere")
    
    print("\n📂 ARCHIVOS EN actualizacion_pythonanywhere/:")
    if os.path.exists('actualizacion_pythonanywhere'):
        for archivo in os.listdir('actualizacion_pythonanywhere'):
            print(f"   📄 {archivo}")
    
    print("\n🎯 URLs QUE FUNCIONARÁN DESPUÉS:")
    print("   🇨🇱 https://e-garage-atlantareciclajes.pythonanywhere.com/bienvenida/cl/")
    print("   🇺🇸 https://e-garage-atlantareciclajes.pythonanywhere.com/bienvenida/usa/")
    print("   🇺🇸 https://e-garage-atlantareciclajes.pythonanywhere.com/welcome/us/")

if __name__ == "__main__":
    try:
        update_dir = crear_paquete_actualizacion()
        generar_instrucciones_deploy()
        mostrar_resumen()
        
        print(f"\n✅ PAQUETE DE ACTUALIZACIÓN CREADO EN: {update_dir}/")
        print("🚀 Sigue las instrucciones en INSTRUCCIONES_DEPLOY.md")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
