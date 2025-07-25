# ===============================================================
# 🔄 SINCRONIZADOR AUTOMÁTICO PARA PYTHONANYWHERE
# ===============================================================
# Script para actualizar el servidor con cambios locales
# ===============================================================

import os
import shutil
import zipfile
from datetime import datetime

def crear_paquete_deploy_completo():
    """Crear paquete completo para subir al servidor"""
    print("📦 CREANDO PAQUETE DE DEPLOY COMPLETO")
    print("=" * 60)
    
    # Crear directorio de deploy
    deploy_dir = "deploy_pythonanywhere"
    if os.path.exists(deploy_dir):
        shutil.rmtree(deploy_dir)
    os.makedirs(deploy_dir, exist_ok=True)
    
    # Crear estructura de directorios
    dirs_crear = [
        f"{deploy_dir}/gestion_taller",
        f"{deploy_dir}/templates/onboarding",
        f"{deploy_dir}/e_garage"
    ]
    
    for dir_path in dirs_crear:
        os.makedirs(dir_path, exist_ok=True)
        print(f"📁 Creado: {dir_path}")
    
    return deploy_dir

def copiar_archivos_actualizados(deploy_dir):
    """Copiar todos los archivos que necesitan actualizarse"""
    print("\n📋 COPIANDO ARCHIVOS ACTUALIZADOS:")
    
    archivos_copiar = [
        # URLs principales
        {
            'origen': 'gestion_taller/urls.py',
            'destino': f'{deploy_dir}/gestion_taller/urls.py',
            'descripcion': 'URLs con rutas de bienvenida'
        },
        # Configuración de producción
        {
            'origen': 'e_garage/settings_production.py',
            'destino': f'{deploy_dir}/e_garage/settings_production.py',
            'descripcion': 'Configuración de producción'
        },
        # WSGI de producción
        {
            'origen': 'wsgi_production.py',
            'destino': f'{deploy_dir}/wsgi_production.py',
            'descripcion': 'WSGI configurado'
        },
        # Requirements
        {
            'origen': 'requirements.txt',
            'destino': f'{deploy_dir}/requirements.txt',
            'descripcion': 'Dependencias actualizadas'
        },
        # Plantillas de bienvenida
        {
            'origen': 'templates/onboarding/bienvenida_chile.html',
            'destino': f'{deploy_dir}/templates/onboarding/bienvenida_chile.html',
            'descripcion': 'Plantilla bienvenida Chile'
        },
        {
            'origen': 'templates/onboarding/bienvenida_usa.html',
            'destino': f'{deploy_dir}/templates/onboarding/bienvenida_usa.html',
            'descripcion': 'Plantilla bienvenida USA'
        }
    ]
    
    archivos_copiados = 0
    for archivo in archivos_copiar:
        if os.path.exists(archivo['origen']):
            shutil.copy2(archivo['origen'], archivo['destino'])
            print(f"✅ {archivo['descripcion']}")
            print(f"   📂 {archivo['origen']} → {archivo['destino']}")
            archivos_copiados += 1
        else:
            print(f"⚠️  {archivo['origen']} - No encontrado, omitiendo")
    
    print(f"\n📊 Total archivos copiados: {archivos_copiados}")
    return archivos_copiados

def crear_script_upload():
    """Crear script de comandos para upload automático"""
    script_content = """
# ===============================================================
# 🚀 COMANDOS DE UPLOAD PARA PYTHONANYWHERE
# ===============================================================

## 📂 ESTRUCTURA EN EL SERVIDOR:
/home/atlantareciclajes/e-garage-atlantareciclajes/

## 🔄 ARCHIVOS A SUBIR:

### 1. URLs principales (CRÍTICO)
   Subir: deploy_pythonanywhere/gestion_taller/urls.py
   Destino: /home/atlantareciclajes/e-garage-atlantareciclajes/gestion_taller/urls.py

### 2. Plantillas HTML (NUEVO)
   Crear directorio: /home/atlantareciclajes/e-garage-atlantareciclajes/templates/onboarding/
   Subir: deploy_pythonanywhere/templates/onboarding/bienvenida_chile.html
   Subir: deploy_pythonanywhere/templates/onboarding/bienvenida_usa.html

### 3. Configuración de producción (OPCIONAL)
   Subir: deploy_pythonanywhere/e_garage/settings_production.py
   Destino: /home/atlantareciclajes/e-garage-atlantareciclajes/e_garage/settings_production.py

### 4. WSGI y Requirements (OPCIONAL)
   Subir: deploy_pythonanywhere/wsgi_production.py
   Subir: deploy_pythonanywhere/requirements.txt

## ⚡ COMANDO RÁPIDO:
1. Subir SOLO urls.py y las 2 plantillas HTML
2. Web → Reload
3. Probar URLs: /bienvenida/cl/ y /bienvenida/usa/

## 🎯 URLs QUE FUNCIONARÁN:
✅ https://e-garage-atlantareciclajes.pythonanywhere.com/bienvenida/cl/
✅ https://e-garage-atlantareciclajes.pythonanywhere.com/bienvenida/usa/
✅ https://e-garage-atlantareciclajes.pythonanywhere.com/welcome/us/
"""
    
    with open('deploy_pythonanywhere/COMANDOS_UPLOAD.md', 'w', encoding='utf-8') as f:
        f.write(script_content)
    
    print("✅ Script de upload creado: deploy_pythonanywhere/COMANDOS_UPLOAD.md")

def crear_zip_deploy():
    """Crear ZIP con todos los archivos para upload fácil"""
    print("\n📦 CREANDO ZIP PARA UPLOAD:")
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    zip_name = f"egarage_update_{timestamp}.zip"
    
    with zipfile.ZipFile(zip_name, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk('deploy_pythonanywhere'):
            for file in files:
                file_path = os.path.join(root, file)
                arc_name = os.path.relpath(file_path, 'deploy_pythonanywhere')
                zipf.write(file_path, arc_name)
                print(f"📄 Agregado al ZIP: {arc_name}")
    
    print(f"✅ ZIP creado: {zip_name}")
    return zip_name

def mostrar_instrucciones_finales(zip_name):
    """Mostrar instrucciones finales para el usuario"""
    print("\n" + "=" * 60)
    print("🎯 INSTRUCCIONES FINALES")
    print("=" * 60)
    
    print(f"""
🚀 OPCIÓN 1 - UPLOAD MANUAL (RECOMENDADO):
1. Ir a PythonAnywhere → Files
2. Subir archivos de deploy_pythonanywhere/ a las rutas correctas
3. Web → Reload

📦 OPCIÓN 2 - UPLOAD ZIP:
1. Subir {zip_name} a PythonAnywhere
2. Extraer y mover archivos a las rutas correctas
3. Web → Reload

🎯 ARCHIVOS CRÍTICOS (MÍNIMO NECESARIO):
✅ gestion_taller/urls.py
✅ templates/onboarding/bienvenida_chile.html  
✅ templates/onboarding/bienvenida_usa.html

📱 VERIFICACIÓN:
Después del reload, probar:
🇨🇱 https://e-garage-atlantareciclajes.pythonanywhere.com/bienvenida/cl/
🇺🇸 https://e-garage-atlantareciclajes.pythonanywhere.com/bienvenida/usa/

💡 Si hay errores: Web → Error log
""")

def main():
    """Función principal"""
    print("🔄 SINCRONIZADOR PYTHONANYWHERE - eGARAGE")
    print("=" * 60)
    
    try:
        # Crear directorio de deploy
        deploy_dir = crear_paquete_deploy_completo()
        
        # Copiar archivos actualizados
        archivos_copiados = copiar_archivos_actualizados(deploy_dir)
        
        if archivos_copiados == 0:
            print("❌ No se copiaron archivos. Verificar rutas.")
            return
        
        # Crear script de upload
        crear_script_upload()
        
        # Crear ZIP
        zip_name = crear_zip_deploy()
        
        # Mostrar instrucciones
        mostrar_instrucciones_finales(zip_name)
        
        print("\n✅ PAQUETE DE DEPLOY LISTO")
        print(f"📁 Directorio: deploy_pythonanywhere/")
        print(f"📦 ZIP: {zip_name}")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")

if __name__ == "__main__":
    main()
